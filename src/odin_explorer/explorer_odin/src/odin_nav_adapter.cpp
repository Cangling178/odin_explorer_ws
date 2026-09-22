// 将隔离后的厂商位姿和点云接入二维导航；不发送任何底盘指令。
#include <array>
#include <cmath>
#include <cstring>
#include <memory>
#include <limits>
#include <stdexcept>
#include <vector>
#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <pcl_conversions/pcl_conversions.h>
#include <pcl/common/transforms.h>
#include <pcl/filters/crop_box.h>
#include <pcl/filters/filter.h>
#include <pcl/filters/passthrough.h>
#include <tf2/LinearMath/Transform.h>
#include <tf2/utils.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.hpp>
#include <tf2_msgs/msg/tf_message.hpp>
#include <tf2_ros/transform_broadcaster.h>
#include <tf2_ros/static_transform_broadcaster.h>
#include "small_obstacle_filter.hpp"

class OdinNavAdapter : public rclcpp::Node
{
public:
  OdinNavAdapter() : Node("odin_nav_adapter")
  {
    // 参数表示父坐标系内的子坐标系位姿，依次为 x、y、z、roll、pitch、yaw。
    base_imu_ = parameter_transform("base_to_imu");
    map_vendor_map_ = parameter_transform("map_from_odin");
    min_height_ = declare_parameter("obstacle_min_z", 0.02);
    max_height_ = declare_parameter("obstacle_max_z", 1.2);
    floor_z_ = declare_parameter("floor_z_in_base", -0.03325);
    cluster_tolerance_ = declare_parameter("small_cluster_tolerance", 0.04);
    small_cluster_extent_ = declare_parameter("small_cluster_max_extent", 0.25);
    small_cluster_max_z_ = declare_parameter("small_cluster_max_z", 0.04);
    if (!std::isfinite(cluster_tolerance_) || cluster_tolerance_ <= 0.0 ||
        !std::isfinite(small_cluster_extent_) || small_cluster_extent_ < 0.0 ||
        !std::isfinite(small_cluster_max_z_)) {
      throw std::invalid_argument("小障碍过滤参数无效");
    }
    self_box_ = declare_parameter<std::vector<double>>("self_box", {-0.06, 0.25, -0.16, 0.16, -0.04, 0.20});
    if (self_box_.size() != 6 || !std::isfinite(min_height_) ||
        !std::isfinite(max_height_) || !std::isfinite(floor_z_) ||
        max_height_ <= min_height_ || floor_z_ >= min_height_) {
      throw std::invalid_argument("点云范围、地面高度或车体包络参数无效");
    }
    for (double v : self_box_) {if (!std::isfinite(v)) {throw std::invalid_argument("车体包络必须为有限数值");}}
    for (int i = 0; i < 6; i += 2) {
      if (self_box_[i] >= self_box_[i + 1]) {throw std::invalid_argument("车体包络下限必须小于上限");}
    }
    broadcaster_ = std::make_unique<tf2_ros::TransformBroadcaster>(*this);
    static_broadcaster_ = std::make_unique<tf2_ros::StaticTransformBroadcaster>(*this);
    static_broadcaster_->sendTransform(message(base_imu_, "base_link", "odin_imu", now()));
    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("/odom", 10);
    obstacles_pub_ = create_publisher<sensor_msgs::msg::PointCloud2>("/navigation/obstacle_points", rclcpp::SensorDataQoS());
    rays_pub_ = create_publisher<sensor_msgs::msg::PointCloud2>("/navigation/clearing_points", rclcpp::SensorDataQoS());
    auto tf_callback = [this](tf2_msgs::msg::TFMessage::ConstSharedPtr msg) {receive_tf(*msg);};
    tf_sub_ = create_subscription<tf2_msgs::msg::TFMessage>("/odin_vendor/tf", rclcpp::QoS(100).best_effort(), tf_callback);
    static_sub_ = create_subscription<tf2_msgs::msg::TFMessage>("/odin_vendor/tf_static", rclcpp::QoS(100).transient_local(), tf_callback);
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>("/odin1/odometry", rclcpp::SensorDataQoS(),
      [this](nav_msgs::msg::Odometry::ConstSharedPtr msg) {receive_odom(*msg);});
    // 厂商以 Reliable 发布大帧点云；请求可靠重传，避免 UDP 丢包使导航障碍更新停顿。
    cloud_sub_ = create_subscription<sensor_msgs::msg::PointCloud2>("/odin1/cloud_raw", rclcpp::SensorDataQoS().reliable(),
      [this](sensor_msgs::msg::PointCloud2::ConstSharedPtr msg) {receive_cloud(*msg);});
  }

private:
  tf2::Transform parameter_transform(const std::string & name)
  {
    auto v = declare_parameter<std::vector<double>>(name, std::vector<double>{});
    if (v.size() != 6) {throw std::invalid_argument(name + " 必须填写实测的六个数值");}
    for (double x : v) {if (!std::isfinite(x)) {throw std::invalid_argument(name + " 存在非有限值");}}
    tf2::Quaternion q; q.setRPY(v[3], v[4], v[5]);
    return tf2::Transform(q, tf2::Vector3(v[0], v[1], v[2]));
  }
  static bool valid(const tf2::Transform & t)
  {
    const auto & p = t.getOrigin();
    return std::isfinite(p.x()) && std::isfinite(p.y()) && std::isfinite(p.z()) &&
      std::isfinite(t.getRotation().length2()) && t.getRotation().length2() > 0.5;
  }
  static tf2::Transform planar(const tf2::Transform & t)
  {
    tf2::Quaternion q; q.setRPY(0, 0, tf2::getYaw(t.getRotation()));
    return tf2::Transform(q, tf2::Vector3(t.getOrigin().x(), t.getOrigin().y(), 0));
  }
  static geometry_msgs::msg::TransformStamped message(const tf2::Transform & t,
    const std::string & parent, const std::string & child, const rclcpp::Time & stamp)
  {
    geometry_msgs::msg::TransformStamped out;
    out.header.stamp = stamp; out.header.frame_id = parent; out.child_frame_id = child;
    out.transform = tf2::toMsg(t); return out;
  }
  void receive_tf(const tf2_msgs::msg::TFMessage & msg)
  {
    for (const auto & item : msg.transforms) {
      tf2::Transform t; tf2::fromMsg(item.transform, t);
      if (!valid(t)) {continue;}
      if (item.header.frame_id == "odom" && item.child_frame_id == "map") {
        // 厂商给出 T_odom_map，求逆后才是 T_map_odom；不能只交换帧名称。
        vendor_map_odom_ = t.inverse(); have_map_ = true;
      } else if (item.header.frame_id == "imu" && item.child_frame_id == "lidar") {
        // 此项是设备内部刚性外参，虽由厂商动态发布，导航中只作为静态外参。
        if (!have_lidar_) {
          base_lidar_ = base_imu_ * t;
          static_broadcaster_->sendTransform(message(t, "odin_imu", "odin_lidar", now()));
          have_lidar_ = true;
        }
      }
    }
  }
  void receive_odom(const nav_msgs::msg::Odometry & input)
  {
    if (input.header.frame_id != "odom" || input.child_frame_id != "imu") {return;}
    tf2::Transform vendor_odom_imu; tf2::fromMsg(input.pose.pose, vendor_odom_imu);
    if (!valid(vendor_odom_imu)) {return;}
    const rclcpp::Time stamp(input.header.stamp);
    if (stamp.nanoseconds() <= last_stamp_) {return;}
    const auto vendor_odom_base = vendor_odom_imu * base_imu_.inverse();
    const auto odom_base = planar(vendor_odom_base);
    std::vector<geometry_msgs::msg::TransformStamped> transforms;
    transforms.push_back(message(odom_base, "odom", "base_link", stamp));
    if (have_map_) {
      // 地图修正在两次厂商更新之间保持；局部 odom 不受全局重定位跳变影响。
      auto map_base = planar(map_vendor_map_ * vendor_map_odom_ * vendor_odom_base);
      transforms.push_back(message(map_base * odom_base.inverse(), "map", "odom", stamp));
    }
    broadcaster_->sendTransform(transforms);
    nav_msgs::msg::Odometry output;
    output.header.stamp = stamp; output.header.frame_id = "odom"; output.child_frame_id = "base_link";
    tf2::toMsg(odom_base, output.pose.pose);
    // 厂商旧固件可能不填速度；对连续车体位姿求差分，避免把传感器速度误作车体速度。
    if (last_stamp_ > 0) {
      double dt = (stamp.nanoseconds() - last_stamp_) * 1e-9;
      if (dt > 0.001 && dt < 0.5) {
        auto delta = odom_base.getBasis().transpose() * (odom_base.getOrigin() - last_pose_.getOrigin());
        output.twist.twist.linear.x = delta.x() / dt;
        output.twist.twist.linear.y = delta.y() / dt;
        double yaw_delta = tf2::getYaw(odom_base.getRotation()) - tf2::getYaw(last_pose_.getRotation());
        output.twist.twist.angular.z = std::atan2(std::sin(yaw_delta), std::cos(yaw_delta)) / dt;
      }
    }
    last_stamp_ = stamp.nanoseconds(); last_pose_ = odom_base;
    // 不复制厂商协方差：旧协议可能在这些字段中承载内部矩阵，而非统计协方差。
    odom_pub_->publish(output);
  }
  static Eigen::Matrix4f matrix(const tf2::Transform & t)
  {
    Eigen::Matrix4f m = Eigen::Matrix4f::Identity();
    for (int row = 0; row < 3; ++row) {
      for (int col = 0; col < 3; ++col) {m(row, col) = t.getBasis()[row][col];}
      m(row, 3) = t.getOrigin()[row];
    }
    return m;
  }
  void receive_cloud(const sensor_msgs::msg::PointCloud2 & input)
  {
    if (!have_lidar_ || input.header.frame_id != "lidar" || input.is_bigendian) {return;}
    // 验证字段和缓冲区长度后交给开源 PCL，避免错误消息破坏转换过程。
    int found = 0;
    for (const auto * name : {"x", "y", "z"}) {
      for (const auto & field : input.fields) {
        if (field.name == name && field.datatype == sensor_msgs::msg::PointField::FLOAT32 &&
          field.count == 1 && uint64_t(field.offset) + 4 <= input.point_step) {++found; break;}
      }
    }
    if (found != 3 || uint64_t(input.row_step) < uint64_t(input.width) * input.point_step ||
      input.data.size() < uint64_t(input.row_step) * input.height) {return;}
    using Cloud = pcl::PointCloud<pcl::PointXYZ>;
    auto body = std::make_shared<Cloud>();
    pcl::fromROSMsg(input, *body);
    // 强制检查 NaN，即使上游错误地将 is_dense 设置为 true。
    body->is_dense = false;
    std::vector<int> indices;
    pcl::removeNaNFromPointCloud(*body, *body, indices);
    pcl::transformPointCloud(*body, *body, matrix(base_lidar_));
    // PCL CropBox 去除车体自身；PassThrough 按车体高度选取障碍和清除回波。
    auto outside = std::make_shared<Cloud>();
    pcl::CropBox<pcl::PointXYZ> crop;
    crop.setInputCloud(body); crop.setNegative(true);
    crop.setMin(Eigen::Vector4f(self_box_[0], self_box_[2], self_box_[4], 1));
    crop.setMax(Eigen::Vector4f(self_box_[1], self_box_[3], self_box_[5], 1));
    crop.filter(*outside);
    pcl::PassThrough<pcl::PointXYZ> pass;
    pass.setInputCloud(outside); pass.setFilterFieldName("z");
    auto publish = [&](double lower, double upper, auto publisher, bool filter_small) {
      Cloud filtered, sensor;
      pass.setFilterLimits(lower, upper); pass.filter(filtered);
      if (filter_small) {
        filtered = explorer_odin::filter_small_obstacles(
          filtered, cluster_tolerance_, small_cluster_extent_, small_cluster_max_z_);
      }
      // 回到真实雷达原点，Nav2 三维射线清除不能错误地从 base_link 发出。
      pcl::transformPointCloud(filtered, sensor, matrix(base_lidar_.inverse()));
      sensor_msgs::msg::PointCloud2 out; pcl::toROSMsg(sensor, out);
      out.header = input.header; out.header.frame_id = "odin_lidar";
      publisher->publish(out);
    };
    publish(min_height_, max_height_, obstacles_pub_, true);
    // 地面不标记为障碍，但保留真实回波用于 VoxelLayer 的三维射线清除。
    // 清除回波不受障碍高度上限裁剪：远处高点的射线也能穿过近处旧障碍。
    publish(floor_z_ - 0.03, std::numeric_limits<float>::max(), rays_pub_, false);
  }
  tf2::Transform base_imu_, base_lidar_, map_vendor_map_, vendor_map_odom_, last_pose_;
  bool have_map_{false}, have_lidar_{false};
  int64_t last_stamp_{0};
  double min_height_, max_height_, floor_z_;
  double cluster_tolerance_, small_cluster_extent_, small_cluster_max_z_;
  std::vector<double> self_box_;
  std::unique_ptr<tf2_ros::TransformBroadcaster> broadcaster_;
  std::unique_ptr<tf2_ros::StaticTransformBroadcaster> static_broadcaster_;
  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_;
  rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr obstacles_pub_, rays_pub_;
  rclcpp::Subscription<tf2_msgs::msg::TFMessage>::SharedPtr tf_sub_, static_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr cloud_sub_;
};
int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  try {rclcpp::spin(std::make_shared<OdinNavAdapter>());}
  catch (const std::exception & e) {RCLCPP_FATAL(rclcpp::get_logger("odin_nav_adapter"), "%s", e.what()); rclcpp::shutdown(); return 1;}
  rclcpp::shutdown(); return 0;
}
