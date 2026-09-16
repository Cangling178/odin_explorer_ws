// Odin FishPoly resampling of Gazebo Classic's equidistant cubemap rendering.
// Model reference: manifoldsdk/odin_ros_driver/include/polynomial_camera.hpp.
// Keep geometry and the custom CameraInfo contract in sync with fishpoly.py.
#include <gazebo/common/Plugin.hh>
#include <gazebo/sensors/CameraSensor.hh>
#include <gazebo/rendering/WideAngleCamera.hh>
#include <gazebo_ros/node.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/camera_info.hpp>
#include <opencv2/imgproc.hpp>
#include <array>
#include <chrono>
#include <cmath>
#include <functional>
#include <sstream>
#include <stdexcept>

namespace odin_sim
{
class FishPolyCamera : public gazebo::SensorPlugin
{
public:
  ~FishPolyCamera() override { connection_.reset(); }

  void Load(gazebo::sensors::SensorPtr sensor, sdf::ElementPtr sdf) override
  {
    // Avoid a large OpenCV worker pool competing with Gazebo sensor threads.
    cv::setNumThreads(1);
    node_ = gazebo_ros::Node::Get(sdf);
    try {
      sensor_ = std::dynamic_pointer_cast<gazebo::sensors::CameraSensor>(sensor);
      if (!sensor_ || !boost::dynamic_pointer_cast<gazebo::rendering::WideAngleCamera>(sensor_->Camera()))
        throw std::runtime_error("FishPoly requires a wideanglecamera sensor");
      auto camera = sensor_->Camera();
      if (camera->ImageWidth() != camera->ImageHeight() ||
          std::abs(camera->HFOV().Radian()-M_PI) > 1e-5)
        throw std::runtime_error("Expected square 180 degree intermediate rendering, got " + std::to_string(camera->ImageWidth()) + "x" + std::to_string(camera->ImageHeight()) + " hfov=" + std::to_string(camera->HFOV().Radian()));
      auto wide = boost::dynamic_pointer_cast<gazebo::rendering::WideAngleCamera>(camera);
      if (wide->Lens()->Type() != "equidistant" || !wide->Lens()->ScaleToHFOV())
        throw std::runtime_error("Expected scaled equidistant rendering lens");
      info_.width = sdf->Get<unsigned int>("width");
      info_.height = sdf->Get<unsigned int>("height");
      info_.header.frame_id = sdf->Get<std::string>("frame_name");
      std::istringstream intrinsics(sdf->Get<std::string>("intrinsics"));
      for (auto &v : info_.k)
        if (!(intrinsics >> v) || !std::isfinite(v)) throw std::runtime_error("Invalid intrinsics");
      std::istringstream coefficients(sdf->Get<std::string>("coefficients"));
      info_.d.resize(6);
      for (auto &v : info_.d)
        if (!(coefficients >> v) || !std::isfinite(v)) throw std::runtime_error("Invalid coefficients");
      if (info_.width < 2 || info_.height < 2 || info_.k[0] <= 0 || info_.k[4] <= 0)
        throw std::runtime_error("Invalid calibration dimensions/scales");
      info_.distortion_model = "fishpoly";
      info_.r = {1, 0, 0, 0, 1, 0, 0, 0, 1};
      // P stays zero: this plugin does not publish a rectified pinhole image.
      const unsigned size = camera->ImageWidth();
      cv::Mat mx(info_.height, info_.width, CV_32FC1);
      cv::Mat my(info_.height, info_.width, CV_32FC1);
      const double focal = size/camera->HFOV().Radian();
      for (unsigned v = 0; v < info_.height; ++v) {
        for (unsigned u = 0; u < info_.width; ++u) {
          const double y = (v-info_.k[5])/info_.k[4];
          const double x = (u-info_.k[2]-info_.k[1]*y)/info_.k[0];
          const double radius = std::hypot(x, y);
          if (radius >= Radius(M_PI/2)) throw std::runtime_error("Calibration exceeds forward hemisphere");
          double lo = 0, hi = M_PI/2;
          for (int i = 0; i < 48; ++i) {
            const double mid = (lo+hi)/2;
            if (Radius(mid) < radius) lo = mid; else hi = mid;
          }
          const double theta = (lo+hi)/2;
          // Stay clear of the stock wide-angle shader's cutoff feathering.
          if (theta > M_PI/2-0.04) throw std::runtime_error("Calibration too close to render cutoff");
          const double scale = radius > 1e-15 ? focal*theta/radius : focal;
          // Fragment centers in Gazebo span (i+0.5)/size; OpenCV uses integer centers.
          const double su = size/2.0-0.5 + scale*x;
          const double sv = size/2.0-0.5 + scale*y;
          if (su < 1 || sv < 1 || su >= size-2 || sv >= size-2)
            throw std::runtime_error("FishPoly ray outside render texture");
          mx.at<float>(v, u) = static_cast<float>(su);
          my.at<float>(v, u) = static_cast<float>(sv);
        }
      }
      cv::convertMaps(mx, my, map1_, map2_, CV_16SC2);
      image_.width = info_.width;
      image_.height = info_.height;
      image_.encoding = "rgb8";
      image_.is_bigendian = false;
      image_.step = info_.width*3;
      image_.data.resize(image_.step*image_.height);
      image_.header.frame_id = info_.header.frame_id;
      image_pub_ = node_->create_publisher<sensor_msgs::msg::Image>("image", rclcpp::QoS(5));
      info_pub_ = node_->create_publisher<sensor_msgs::msg::CameraInfo>("camera_info", rclcpp::QoS(5));
      connection_ = camera->ConnectNewImageFrame(std::bind(&FishPolyCamera::OnImage, this,
        std::placeholders::_1, std::placeholders::_2, std::placeholders::_3,
        std::placeholders::_4, std::placeholders::_5));
      sensor_->SetActive(true);
      RCLCPP_INFO(node_->get_logger(), "FishPoly ready: %ux%u, full calibrated frame", info_.width, info_.height);
    } catch (const std::exception &e) {
      RCLCPP_FATAL(node_->get_logger(), "FishPoly camera failed: %s", e.what());
      throw;
    }
  }

private:
  double Radius(double theta) const
  {
    double p = info_.d[5];
    for (int i = 4; i >= 0; --i) p = info_.d[i]+theta*p;
    return theta*(1+theta*p);
  }

  void OnImage(const unsigned char *data, unsigned width, unsigned height,
               unsigned depth, const std::string &)
  {
    if (depth != 3 || !data) return;
    const auto begin = std::chrono::steady_clock::now();
    cv::Mat source(height, width, CV_8UC3, const_cast<unsigned char *>(data));
    cv::Mat output(info_.height, info_.width, CV_8UC3, image_.data.data());
    cv::remap(source, output, map1_, map2_, cv::INTER_LINEAR, cv::BORDER_CONSTANT);
    const auto time = sensor_->LastMeasurementTime();
    const double stamp = time.Double();
    if (last_frame_stamp_ > 0 && stamp-last_frame_stamp_ > .15)
      RCLCPP_WARN(node_->get_logger(), "FishPoly source frame gap %.3f simulated seconds", stamp-last_frame_stamp_);
    last_frame_stamp_ = stamp;
    image_.header.stamp.sec = time.sec;
    image_.header.stamp.nanosec = time.nsec;
    info_.header.stamp = image_.header.stamp;
    image_pub_->publish(image_);
    info_pub_->publish(info_);
    const double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now()-begin).count();
    if (elapsed > .1) RCLCPP_WARN(node_->get_logger(), "FishPoly frame processing/publish took %.3f s", elapsed);
  }

  gazebo_ros::Node::SharedPtr node_;
  gazebo::sensors::CameraSensorPtr sensor_;
  sensor_msgs::msg::CameraInfo info_;
  sensor_msgs::msg::Image image_;
  cv::Mat map1_, map2_;
  double last_frame_stamp_ = 0;
  rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr image_pub_;
  rclcpp::Publisher<sensor_msgs::msg::CameraInfo>::SharedPtr info_pub_;
  gazebo::event::ConnectionPtr connection_;
};
GZ_REGISTER_SENSOR_PLUGIN(FishPolyCamera)
}  // namespace odin_sim
