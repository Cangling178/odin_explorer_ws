#include "racer_perception/line_geometry.hpp"
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/camera_info.hpp>
#include <nav_msgs/msg/path.hpp>
#include <std_msgs/msg/string.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <tf2/LinearMath/Transform.h>
#include <cv_bridge/cv_bridge.h>
#include <deque>
#include <chrono>
#include <racer_interfaces/msg/line_observation.hpp>

class LinePerception : public rclcpp::Node {
 public:
  LinePerception() : Node("line_perception"), buffer_(get_clock()), listener_(buffer_) {
    // Small ground grids run with bounded OpenCV scheduling overhead.
    cv::setNumThreads(1);
    grid_.near_x = declare_parameter("near_x", .10);
    grid_.far_x = declare_parameter("far_x", .75);
    grid_.half_width = declare_parameter("half_width", .50);
    grid_.step = declare_parameter("grid_step", .005);
    grid_.ground_z = declare_parameter("ground_z", -.03325);
    grid_.validate();
    threshold_ = declare_parameter("black_threshold", 65.);
    min_width_ = declare_parameter("min_line_width", .008);
    max_width_ = declare_parameter("max_line_width", .05);
    min_length_ = declare_parameter("min_visible_length", .10);
    seed_limit_ = declare_parameter("seed_lateral_limit", .45);
    min_confidence_ = declare_parameter("min_confidence", .5);
    max_age_ = declare_parameter("max_image_age", .35);
    frame_ = declare_parameter("base_frame", std::string("base_link"));
    for (double v : {threshold_, min_width_, max_width_, min_length_, seed_limit_, min_confidence_, max_age_})
      if (!std::isfinite(v) || v <= 0) throw std::invalid_argument("Invalid detector parameter");
    if (threshold_ >= 255 || max_width_ <= min_width_ || min_confidence_ > 1 ||
        min_length_ > grid_.far_x-grid_.near_x || frame_.empty()) throw std::invalid_argument("Invalid detector range");
    observation_pub_ = create_publisher<racer_interfaces::msg::LineObservation>("observation", 1);
    mask_pub_ = create_publisher<sensor_msgs::msg::Image>("black_mask", 1);
    gray_pub_ = create_publisher<sensor_msgs::msg::Image>("ground_gray", 1);
    path_pub_ = create_publisher<nav_msgs::msg::Path>("local_path", 1);
    status_pub_ = create_publisher<std_msgs::msg::String>("perception_status", 1);
    debug_pub_ = create_publisher<sensor_msgs::msg::Image>("ground_debug", 1);
    // Match exact image/info stamps without retaining a deep queue of large images.
    info_sub_ = create_subscription<sensor_msgs::msg::CameraInfo>("camera_info", 5,
      [this](sensor_msgs::msg::CameraInfo::ConstSharedPtr info) {
        infos_.push_back(info); if (infos_.size() > 5) infos_.pop_front(); try_process();
      });
    image_sub_ = create_subscription<sensor_msgs::msg::Image>("image", rclcpp::SensorDataQoS().keep_last(3),
      [this](sensor_msgs::msg::Image::ConstSharedPtr image) {
        images_.push_back(image); if(images_.size()>3)images_.pop_front(); try_process();
      });
  }
 private:
  void publish_invalid(const std_msgs::msg::Header &header, const std::string &reason) {
    nav_msgs::msg::Path path; path.header = header; path.header.frame_id = frame_;
    path_pub_->publish(path);
    racer_interfaces::msg::LineObservation observation; observation.path = path; observation.reason = reason;
    observation_pub_->publish(observation); hint_.valid = false;
    std_msgs::msg::String status; status.data = reason; status_pub_->publish(status);
  }
  void try_process() {
    sensor_msgs::msg::Image::ConstSharedPtr image;
    sensor_msgs::msg::CameraInfo::ConstSharedPtr info;
    // Independent DDS streams may deliver the next image before the previous
    // CameraInfo. Match the newest complete pair without starving older pairs.
    for(auto it=images_.rbegin();it!=images_.rend() && !info;++it) {
      for(const auto &candidate:infos_)if(candidate->header.stamp==(*it)->header.stamp) {
        image=*it;info=candidate;break;
      }
    }
    if(!info)return;
    while(!images_.empty()) {
      auto front=images_.front();images_.pop_front();if(front==image)break;
    }
    const auto processing_start=std::chrono::steady_clock::now();
    try {
      double age = (now()-rclcpp::Time(image->header.stamp)).seconds();
      if (age < -.02 || age > max_age_ || rclcpp::Time(image->header.stamp).nanoseconds() <= 0)
        throw std::runtime_error("stale_or_future_image");
      if (info->header.frame_id != image->header.frame_id || image->header.frame_id.empty() ||
          info->width != image->width || info->height != image->height ||
          info->distortion_model != "fishpoly" || info->binning_x > 1 || info->binning_y > 1 ||
          info->roi.width || info->roi.height || info->roi.x_offset || info->roi.y_offset)
        throw std::runtime_error("incompatible_camera_info");
      racer_perception::FishPoly camera{info->k, info->d}; camera.validate();
      auto transform = buffer_.lookupTransform(image->header.frame_id, frame_, image->header.stamp,
                                               rclcpp::Duration::from_seconds(.04)).transform;
      tf2::Transform camera_from_base(tf2::Quaternion(transform.rotation.x, transform.rotation.y,
        transform.rotation.z, transform.rotation.w), tf2::Vector3(transform.translation.x,
        transform.translation.y, transform.translation.z));
      cv::Mat map_x(grid_.rows(), grid_.cols(), CV_32FC1), map_y(map_x.size(), CV_32FC1);
      cv::Mat visible(map_x.size(), CV_8UC1, cv::Scalar(0));
      for (int row = 0; row < map_x.rows; ++row) for (int col = 0; col < map_x.cols; ++col) {
        auto p = grid_.point(row, col);
        auto ray = camera_from_base*tf2::Vector3(p.x, p.y, grid_.ground_z);
        auto uv = camera.project({ray.x(), ray.y(), ray.z()});
        bool valid = std::isfinite(uv.x) && std::isfinite(uv.y) && uv.x >= 1 && uv.y >= 1 &&
                     uv.x < image->width-2. && uv.y < image->height-2.;
        map_x.at<float>(row, col) = valid ? uv.x : -1;
        map_y.at<float>(row, col) = valid ? uv.y : -1;
        visible.at<unsigned char>(row, col) = valid ? 255 : 0;
      }
      auto source = cv_bridge::toCvShare(image, "mono8");
      cv::Scalar mean, deviation; cv::meanStdDev(source->image, mean, deviation);
      if (deviation[0] < 1.) throw std::runtime_error("blank_or_uniform_image");
      racer_perception::SeedHint hint;
      if (hint_.valid && (rclcpp::Time(image->header.stamp)-hint_stamp_).seconds() < .25) {
        try {
          auto shift = buffer_.lookupTransform(frame_, image->header.stamp, frame_, hint_stamp_, "odom").transform;
          tf2::Transform motion(tf2::Quaternion(shift.rotation.x,shift.rotation.y,shift.rotation.z,shift.rotation.w),
            tf2::Vector3(shift.translation.x,shift.translation.y,shift.translation.z));
          auto a = motion*tf2::Vector3(hint_.point.x,hint_.point.y,0);
          auto b = motion.getBasis()*tf2::Vector3(hint_.direction.x,hint_.direction.y,0);
          hint = {{a.x(),a.y()},{b.x(),b.y()},true};
        } catch (const std::exception &) { hint_.valid=false; }
      }
      cv::Mat ground;
      cv::remap(source->image, ground, map_x, map_y, cv::INTER_LINEAR, cv::BORDER_CONSTANT, cv::Scalar(255));
      auto detection = racer_perception::detect(ground, visible, grid_, threshold_, min_width_,
                                                max_width_, min_length_, seed_limit_, hint);
      if (detection.confidence < min_confidence_ && detection.valid()) detection.reason = "low_confidence";
      nav_msgs::msg::Path path; path.header = image->header; path.header.frame_id = frame_;
      if (detection.valid()) for (const auto &p : detection.points) {
        geometry_msgs::msg::PoseStamped pose; pose.header = path.header;
        pose.pose.position.x = p.x; pose.pose.position.y = p.y; pose.pose.position.z = grid_.ground_z;
        pose.pose.orientation.w = 1; path.poses.push_back(pose);
      }
      path_pub_->publish(path);
      racer_interfaces::msg::LineObservation observation;
      observation.path = path; observation.image_valid = true;
      observation.path_valid = detection.valid(); observation.confidence = detection.confidence;
      observation.reason = detection.reason; observation.exits = detection.exits;
      observation.corner_valid = detection.valid() && detection.corner_valid && detection.exits == 1;
      observation.corner.x = detection.corner.x; observation.corner.y = detection.corner.y;
      observation.exit_direction.x = detection.exit_direction.x; observation.exit_direction.y = detection.exit_direction.y;
      observation_pub_->publish(observation);
      hint_.valid = detection.valid();
      if (hint_.valid) {
        hint_.point = detection.points.front();
        auto direction = detection.points[std::min(size_t(8),detection.points.size()-1)]-hint_.point;
        hint_.direction = direction/cv::norm(direction); hint_stamp_ = rclcpp::Time(image->header.stamp);
      }
      if (mask_pub_->get_subscription_count())
        mask_pub_->publish(*cv_bridge::CvImage(image->header,"mono8",detection.mask).toImageMsg());
      if (gray_pub_->get_subscription_count())
        gray_pub_->publish(*cv_bridge::CvImage(image->header,"mono8",ground).toImageMsg());
      std_msgs::msg::String status;
      status.data = detection.reason + " confidence=" + std::to_string(detection.confidence) + " end=" + detection.end_reason;
      status.data += " processing_ms=" + std::to_string(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-processing_start).count());
      status_pub_->publish(status);
      if (debug_pub_->get_subscription_count()) {
        cv::Mat debug; cv::cvtColor(ground, debug, cv::COLOR_GRAY2BGR);
        for (const auto &p : detection.points)
          cv::circle(debug, {static_cast<int>((grid_.half_width-p.y)/grid_.step),
                            static_cast<int>((p.x-grid_.near_x)/grid_.step)}, 1, {0, 0, 255}, -1);
        if (detection.corner_valid) {
          cv::Point corner(std::lround((grid_.half_width-detection.corner.y)/grid_.step),
                           std::lround((detection.corner.x-grid_.near_x)/grid_.step));
          cv::circle(debug, corner, 4, {0,255,255}, 1);
          cv::arrowedLine(debug, corner, corner+cv::Point(-detection.exit_direction.y*15,detection.exit_direction.x*15), {0,255,0}, 1);
        }
        debug_pub_->publish(*cv_bridge::CvImage(image->header, "bgr8", debug).toImageMsg());
      }
    } catch (const std::exception &e) { publish_invalid(image->header, e.what()); }
  }
  racer_perception::Grid grid_;
  racer_perception::SeedHint hint_;
  rclcpp::Time hint_stamp_{0,0,RCL_ROS_TIME};
  rclcpp::Publisher<racer_interfaces::msg::LineObservation>::SharedPtr observation_pub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr mask_pub_, gray_pub_;
  double threshold_, min_width_, max_width_, min_length_, seed_limit_, min_confidence_, max_age_;
  std::string frame_;
  tf2_ros::Buffer buffer_;
  tf2_ros::TransformListener listener_;
  std::deque<sensor_msgs::msg::Image::ConstSharedPtr> images_;
  std::deque<sensor_msgs::msg::CameraInfo::ConstSharedPtr> infos_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr image_sub_;
  rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr info_sub_;
  rclcpp::Publisher<nav_msgs::msg::Path>::SharedPtr path_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr status_pub_;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr debug_pub_;
};
int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  try { rclcpp::spin(std::make_shared<LinePerception>()); }
  catch (const std::exception &e) { std::cerr << e.what() << '\n'; rclcpp::shutdown(); return 1; }
  rclcpp::shutdown(); return 0;
}
