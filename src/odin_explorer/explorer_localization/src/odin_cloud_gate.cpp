// A sensor-frame-only gateway. Never relabel world-frame or accumulated clouds.
#include <chrono>
#include <cmath>
#include <deque>
#include <memory>
#include <stdexcept>
#include <string>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <std_msgs/msg/string.hpp>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>

using Cloud = sensor_msgs::msg::PointCloud2;

class OdinCloudGate : public rclcpp::Node
{
public:
  OdinCloudGate() : Node("odin_cloud_gate"), buffer_(get_clock()), listener_(buffer_)
  {
    sensor_frame_ = declare_parameter("sensor_frame", "lidar");
    map_frame_ = declare_parameter("map_frame", "odom");
    odom_frame_ = declare_parameter("odom_frame", "odom");
    max_age_ = declare_parameter("max_cloud_age", 0.5);
    future_tolerance_ = declare_parameter("future_tolerance", 0.1);
    const auto rate = declare_parameter("max_rate", 5.0);
    translation_limit_ = declare_parameter("correction_translation_limit", 0.15);
    rotation_limit_ = declare_parameter("correction_rotation_limit", 0.10);
    if (sensor_frame_.empty() || map_frame_.empty() || odom_frame_.empty() ||
      sensor_frame_ == map_frame_ || sensor_frame_ == odom_frame_ ||
      !std::isfinite(rate) || rate <= 0.0 || !std::isfinite(max_age_) || max_age_ <= 0.0 ||
      !std::isfinite(future_tolerance_) || future_tolerance_ < 0.0 ||
      !std::isfinite(translation_limit_) || translation_limit_ <= 0.0 ||
      !std::isfinite(rotation_limit_) || rotation_limit_ <= 0.0)
    {
      throw std::invalid_argument("Invalid frames, timing or correction thresholds");
    }
    if (map_frame_ == odom_frame_) {
      RCLCPP_WARN(get_logger(),
        "Mapping in odom: no independent map/odom correction is available; "
        "vendor loop closures cannot be reliably detected or rebuilt");
    }
    period_ = 1.0 / rate;
    output_ = create_publisher<Cloud>("points", rclcpp::SensorDataQoS());
    status_ = create_publisher<std_msgs::msg::String>(
      "status", rclcpp::QoS(1).reliable().transient_local());
    input_ = create_subscription<Cloud>("cloud_in", rclcpp::SensorDataQoS(),
      [this](Cloud::ConstSharedPtr msg) { receive(msg); });
    timer_ = create_wall_timer(std::chrono::milliseconds(20), [this]() { process(); });
    report("waiting_for_cloud");
  }

private:
  void report(const std::string & state)
  {
    if (state == state_) {return;}
    state_ = state;
    std_msgs::msg::String msg;
    msg.data = state;
    status_->publish(msg);
    RCLCPP_INFO(get_logger(), "%s", state.c_str());
  }

  void halt(const std::string & reason)
  {
    halted_ = true;
    pending_.clear();
    report("halted: " + reason + "; restart the entire mapping launch to start a new map");
    RCLCPP_ERROR(get_logger(), "%s", state_.c_str());
  }

  void receive(Cloud::ConstSharedPtr msg)
  {
    if (halted_) {return;}
    if (msg->header.frame_id != sensor_frame_) {
      report("rejected_frame: expected sensor frame " + sensor_frame_);
      return;
    }
    const rclcpp::Time stamp(msg->header.stamp);
    const double age = (now() - stamp).seconds();
    if (stamp.nanoseconds() <= 0 || age > max_age_ || age < -future_tolerance_) {
      report("rejected_timestamp");
      return;
    }
    if (stamp.nanoseconds() <= last_received_) {
      report("rejected_out_of_order");
      return;
    }
    // Validate layout before passing untrusted binary fields into PCL/OctoMap.
    if (msg->width == 0 || msg->height == 0 || msg->is_bigendian || msg->point_step == 0 ||
      uint64_t(msg->row_step) < uint64_t(msg->width) * msg->point_step ||
      msg->data.size() < uint64_t(msg->row_step) * msg->height)
    {
      report("rejected_layout");
      return;
    }
    for (const auto * name : {"x", "y", "z"}) {
      bool found = false;
      for (const auto & field : msg->fields) {
        if (field.name == name && field.datatype == sensor_msgs::msg::PointField::FLOAT32 &&
          field.count == 1 && uint64_t(field.offset) + 4 <= msg->point_step)
        {
          found = true;
        }
      }
      if (!found) {report("rejected_xyz_fields"); return;}
    }
    last_received_ = stamp.nanoseconds();
    pending_.push_back(msg);
    if (pending_.size() > 10) {pending_.pop_front();}
  }

  void process()
  {
    if (halted_) {return;}
    const auto current = now();
    if (last_clock_ > 0 && current.nanoseconds() < last_clock_) {
      halt("ROS clock moved backwards");
      return;
    }
    last_clock_ = current.nanoseconds();
    while (!pending_.empty()) {
      const auto cloud = pending_.front();
      const rclcpp::Time stamp(cloud->header.stamp);
      if ((current - stamp).seconds() > max_age_) {
        pending_.pop_front();
        report("dropped_stale_cloud_or_missing_tf");
        continue;
      }
      if ((current - stamp).seconds() < 0.0) {return;}
      try {
        // Exact acquisition-time lookups, never a latest-TF fallback.
        buffer_.lookupTransform(map_frame_, sensor_frame_, stamp);
        const auto correction = buffer_.lookupTransform(map_frame_, odom_frame_, stamp);
        const auto & t = correction.transform.translation;
        const auto & q = correction.transform.rotation;
        tf2::Quaternion rotation(q.x, q.y, q.z, q.w);
        if (!std::isfinite(t.x) || !std::isfinite(t.y) || !std::isfinite(t.z) ||
          !std::isfinite(rotation.length2()) || rotation.length2() < 1e-12)
        {
          halt("invalid map/odom transform");
          return;
        }
        rotation.normalize();
        if (have_reference_) {
          const double distance = std::hypot(std::hypot(t.x - reference_x_, t.y - reference_y_),
            t.z - reference_z_);
          if (distance > translation_limit_ ||
            reference_rotation_.angleShortestPath(rotation) > rotation_limit_)
          {
            halt("map/odom correction exceeded threshold (loop closure or relocalization)");
            return;
          }
        } else {
          reference_x_ = t.x; reference_y_ = t.y; reference_z_ = t.z;
          reference_rotation_ = rotation;
          have_reference_ = true;
        }
      } catch (const tf2::TransformException &) {
        report("waiting_for_acquisition_tf");
        return;
      }
      pending_.pop_front();
      if (last_published_ > 0 && double(stamp.nanoseconds() - last_published_) * 1e-9 < period_) {
        continue;
      }
      output_->publish(*cloud);
      last_published_ = stamp.nanoseconds();
      report("mapping");
    }
    if (last_published_ > 0 && double(current.nanoseconds() - last_published_) * 1e-9 > max_age_) {
      report("waiting_for_fresh_cloud");
    }
  }

  tf2_ros::Buffer buffer_;
  tf2_ros::TransformListener listener_;
  std::string sensor_frame_, map_frame_, odom_frame_, state_;
  double max_age_, future_tolerance_, period_, translation_limit_, rotation_limit_;
  double reference_x_{0}, reference_y_{0}, reference_z_{0};
  tf2::Quaternion reference_rotation_;
  bool have_reference_{false}, halted_{false};
  int64_t last_received_{0}, last_published_{0}, last_clock_{0};
  std::deque<Cloud::ConstSharedPtr> pending_;
  rclcpp::Publisher<Cloud>::SharedPtr output_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_;
  rclcpp::Subscription<Cloud>::SharedPtr input_;
  rclcpp::TimerBase::SharedPtr timer_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<OdinCloudGate>());
  rclcpp::shutdown();
  return 0;
}
