#include "racer_control/line_tracker.hpp"
#include <rclcpp/rclcpp.hpp>
#include <nav_msgs/msg/path.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <tf2/LinearMath/Transform.h>
#include <chrono>
#include <iostream>
#include <sstream>
#include <deque>
#include <racer_interfaces/msg/line_observation.hpp>

class LineController : public rclcpp::Node {
 public:
  LineController() : Node("line_controller"), buffer_(get_clock()), listener_(buffer_) {
    speed_ = declare_parameter("speed", .05);
    lookahead_ = declare_parameter("lookahead", .40);
    min_lookahead_ = declare_parameter("min_lookahead", .12);
    max_lookahead_ = declare_parameter("max_lookahead", .45);
    max_yaw_ = declare_parameter("max_yaw_rate", .5);
    acceleration_ = declare_parameter("acceleration", .15);
    yaw_acceleration_ = declare_parameter("yaw_acceleration", .8);
    path_age_ = declare_parameter("max_path_age", .35);
    curve_memory_ = declare_parameter("observed_path_memory", 12.);
    odom_age_ = declare_parameter("max_odom_age", .15);
    wall_age_ = declare_parameter("wall_watchdog", 1.);
    base_ = declare_parameter("base_frame", std::string("base_link"));
    odom_frame_ = declare_parameter("odom_frame", std::string("odom"));
    for (double v : {speed_, lookahead_, max_yaw_, acceleration_, yaw_acceleration_, path_age_, odom_age_, wall_age_, curve_memory_, min_lookahead_, max_lookahead_})
      if (!std::isfinite(v) || v <= 0) throw std::invalid_argument("Invalid positive controller parameter");
    if (speed_ > .2 || max_yaw_ > 1 || acceleration_ > .3 || yaw_acceleration_ > 1.5 ||
        min_lookahead_ < .10 || min_lookahead_ > lookahead_ || lookahead_ > max_lookahead_ || max_lookahead_ > .7 || base_.empty() || odom_frame_.empty())
      throw std::invalid_argument("Controller parameters exceed baseline limits");
    corner_.config.memory_time=declare_parameter("corner_memory_time",18.);
    corner_.config.memory_distance=declare_parameter("corner_memory_distance",.45);
    corner_.config.memory_angle=declare_parameter("corner_memory_angle",1.9);
    corner_.config.approach_speed=declare_parameter("corner_approach_speed",.04);
    corner_.config.turn_rate=declare_parameter("corner_turn_rate",.30);
    corner_.config.stop_distance=declare_parameter("corner_stop_distance",.080);
    for(double v:{corner_.config.memory_time,corner_.config.memory_distance,corner_.config.memory_angle,
                  corner_.config.approach_speed,corner_.config.turn_rate,corner_.config.stop_distance})
      if(!std::isfinite(v)||v<=0)throw std::invalid_argument("Invalid corner parameter");
    if(corner_.config.memory_time>20||corner_.config.memory_distance>.5||corner_.config.memory_angle>2.2||
       corner_.config.approach_speed>speed_||corner_.config.turn_rate>max_yaw_||corner_.config.stop_distance>.10)
      throw std::invalid_argument("Corner parameters exceed bounded low-speed limits");
    command_pub_ = create_publisher<geometry_msgs::msg::TwistStamped>("cmd_vel", 1);
    state_pub_ = create_publisher<std_msgs::msg::String>("tracking_status", rclcpp::QoS(1).transient_local());
    debug_pub_ = create_publisher<std_msgs::msg::String>("control_debug", 1);
    observation_sub_ = create_subscription<racer_interfaces::msg::LineObservation>("observation", 1,
      [this](racer_interfaces::msg::LineObservation::ConstSharedPtr observation) {
        const auto stamp=rclcpp::Time(observation->path.header.stamp);
        if(stamp.nanoseconds()>seen_stamp_ && (pending_.empty() || stamp>rclcpp::Time(pending_.back()->path.header.stamp))) {
          pending_.push_back(observation);
          if(pending_.size()>5) {pending_.clear();image_valid_=false;stop("observation_queue_overflow");}
        }
      });
    odom_sub_ = create_subscription<nav_msgs::msg::Odometry>("odom", rclcpp::SensorDataQoS(),
      [this](nav_msgs::msg::Odometry::ConstSharedPtr odom) {
        const auto &p = odom->pose.pose.position; const auto &q = odom->pose.pose.orientation;
        const double norm = q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w;
        if (odom->header.frame_id != odom_frame_ || odom->child_frame_id != base_ ||
            !std::isfinite(p.x) || !std::isfinite(p.y) || !std::isfinite(p.z) ||
            !std::isfinite(norm) || std::abs(norm-1) > .01 ||
            !std::isfinite(odom->twist.twist.linear.x) || !std::isfinite(odom->twist.twist.angular.z)) {
          odom_.reset(); stop("invalid_odometry"); return;
        }
        // Clock and odometry arrive on independent DDS streams. Reject a
        // late/future or reordered packet without erasing a still-fresh state.
        // compute() independently expires the last accepted state (ROS + wall).
        const auto stamp = rclcpp::Time(odom->header.stamp);
        if (!racer_control::fresh(now().seconds(), stamp.seconds(), odom_age_) ||
            (odom_ && stamp <= rclcpp::Time(odom_->header.stamp))) return;
        odom_ = odom; odom_wall_ = std::chrono::steady_clock::now();
      });
    enable_ = create_service<std_srvs::srv::SetBool>("~/enable",
      [this](const std_srvs::srv::SetBool::Request::SharedPtr request,
             std_srvs::srv::SetBool::Response::SharedPtr response) {
        if (!request->data) { armed_ = false; corner_.reset(); target_valid_=false; curve_align_=false; state_ = "DISARMED"; publish_zero(); response->success = true; }
        else {
          std::string error;
          auto command = compute(error);
          response->success = command.valid;
          armed_ = command.valid;
          if (!command.valid) publish_zero();
          if (command.valid) {
            // Begin the acceleration interval at arming, not at an earlier
            // disarmed tick. A quantized simulation clock may advance between
            // computing READY and publishing its zero command.
            last_tick_=now().seconds();
            armed_ = true; state_ = "RUNNING";
          }
          else state_ = "STOPPED: " + error;
        }
        response->message = state_; publish_state();
      });
    timer_ = create_wall_timer(std::chrono::milliseconds(20), [this]() { tick(); });
    publish_state();
  }
 private:
  void publish_state() { std_msgs::msg::String status; status.data = state_; state_pub_->publish(status); }
  void publish(double v, double w, bool tick_command=false) {
    geometry_msgs::msg::TwistStamped command;
    command.header.stamp = tick_command?rclcpp::Time(static_cast<int64_t>(std::llround(last_tick_*1e9)),RCL_ROS_TIME):now(); command.header.frame_id = base_;
    command.twist.linear.x = v; command.twist.angular.z = w; command_pub_->publish(command);
  }
  void publish_zero(bool tick_command=false) { last_v_ = last_w_ = 0; publish(0, 0, tick_command); }
  void stop(const std::string &reason) {
    corner_.reset(); target_valid_=false; curve_align_=false;
    if (armed_) { armed_ = false; state_ = "STOPPED: " + reason; publish_state(); }
    publish_zero();
  }
  void receive(const racer_interfaces::msg::LineObservation &observation) {
    const auto &path=observation.path;
    const auto stamp=rclcpp::Time(path.header.stamp);
    if(stamp.nanoseconds()>0 && stamp.nanoseconds()<=seen_stamp_)return;
    auto invalidate=[this](const std::string &why){points_.clear();image_valid_=false;stop(why);};
    if(path.header.frame_id!=base_ || !racer_control::fresh(now().seconds(),stamp.seconds(),path_age_) ||
       !observation.image_valid || !std::isfinite(observation.confidence) || observation.exits>1) {
      invalidate("invalid_observation: "+observation.reason);return;
    }
    seen_stamp_=stamp.nanoseconds();
    try {
      auto tf=buffer_.lookupTransform(odom_frame_,base_,stamp,rclcpp::Duration::from_seconds(0)).transform;
      const auto &q=tf.rotation;
      double norm=q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w;
      if(!std::isfinite(norm)||std::abs(norm-1)>.01||!std::isfinite(tf.translation.x)||
         !std::isfinite(tf.translation.y)||!std::isfinite(tf.translation.z)) {
        invalidate("malformed_observation_transform");return;
      }
      tf2::Transform transform(tf2::Quaternion(q.x,q.y,q.z,q.w),tf2::Vector3(tf.translation.x,tf.translation.y,tf.translation.z));
      std::vector<racer_control::Point> local,global;
      for(const auto &pose:path.poses) {
        auto p=pose.pose.position;
        if(pose.header.frame_id!=base_||pose.header.stamp!=path.header.stamp||!std::isfinite(p.z)) {
          invalidate("malformed_path_header");return;
        }
        local.push_back({p.x,p.y});
        auto shifted=transform*tf2::Vector3(p.x,p.y,p.z);global.push_back({shifted.x(),shifted.y()});
      }
      if(observation.path_valid && (!racer_control::ordered_path(local)||observation.confidence<.5)) {
        invalidate("malformed_path");return;
      }
      if(!observation.path_valid && !path.poses.empty()) {invalidate("inconsistent_observation");return;}
      image_valid_=true;health_stamp_=stamp.nanoseconds();path_wall_=std::chrono::steady_clock::now();
      if(observation.path_valid) {
        bool accepted=true;
        points_=curve_align_?global:racer_control::merge_observed_path(points_,global,&accepted);
        if(accepted)path_stamp_=stamp.nanoseconds();
      }
      else {
        const bool clipped=observation.reason=="no_near_seed" || observation.reason=="insufficient_visible_length";
        if(!clipped || (!corner_.active() && !racer_control::fresh(now().seconds(),path_stamp_*1e-9,curve_memory_))) {
          invalidate("line_lost: "+observation.reason);return;
        }
      }
      if(observation.corner_valid && observation.path_valid && observation.confidence>=.6 && observation.exits==1) {
        const auto &c=observation.corner;const auto &e=observation.exit_direction;
        if(!std::isfinite(c.x)||!std::isfinite(c.y)||!std::isfinite(e.x)||!std::isfinite(e.y)||
           std::abs(std::hypot(e.x,e.y)-1)>.05) {invalidate("invalid_corner");return;}
        size_t index=0;double best=1e9;
        for(size_t i=0;i<local.size();++i) {double d=racer_control::distance(local[i],{c.x,c.y});if(d<best){best=d;index=i;}}
        if(best>.02 || index<2) {invalidate("corner_off_path");return;}
        size_t near=index-1;
        while(near>0&&racer_control::distance(local[near],local[index])<.035)--near;
        size_t before=std::min(size_t(3),near);
        // Fit a sufficiently long incoming straight, excluding the clipped seed
        // tip and rounded skeleton elbow. Do not learn heading from two pixels.
        if(racer_control::distance(local[before],local[near])<.12)return;
        double mx=0,my=0;
        for(size_t i=before;i<=near;++i){mx+=local[i].x;my+=local[i].y;}
        double n=near-before+1;mx/=n;my/=n;
        double xx=0,xy=0,yy=0;
        for(size_t i=before;i<=near;++i){double x=local[i].x-mx,y=local[i].y-my;xx+=x*x;xy+=x*y;yy+=y*y;}
        double fitted=.5*std::atan2(2*xy,xx-yy);
        double residual=0;
        for(size_t i=before;i<=near;++i){double d=-(local[i].x-mx)*std::sin(fitted)+(local[i].y-my)*std::cos(fitted);residual+=d*d;}
        if(std::sqrt(residual/n)>.008)return;
        double yaw=std::atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));
        double incoming=fitted+yaw;
        auto world_corner=transform*tf2::Vector3(c.x,c.y,0);
        corner_.observe(stamp.seconds(),{world_corner.x(),world_corner.y()},std::atan2(e.y,e.x)+yaw,incoming,
                        {tf.translation.x,tf.translation.y},yaw);
      } else corner_.no_corner(stamp.seconds());
    } catch(const std::exception &) {invalidate("missing_observation_transform");}
  }
  racer_control::Command compute(std::string &error) {
    const double time=now().seconds();const auto wall=std::chrono::steady_clock::now();
    if(!image_valid_||!racer_control::fresh(time,health_stamp_*1e-9,path_age_)||
       std::chrono::duration<double>(wall-path_wall_).count()>wall_age_) {error=!pending_.empty()?"observation_transform_timeout":"image_timeout_or_invalid";return {};}
    if(!odom_||!racer_control::fresh(time,rclcpp::Time(odom_->header.stamp).seconds(),odom_age_)||
       std::chrono::duration<double>(wall-odom_wall_).count()>wall_age_) {error="odometry_timeout";return {};}
    const auto &p=odom_->pose.pose.position;const auto &q=odom_->pose.pose.orientation;
    double yaw=std::atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));
    tf2::Transform transform(tf2::Quaternion(q.x,q.y,q.z,q.w),tf2::Vector3(p.x,p.y,p.z));
    auto inverse=transform.inverse();std::vector<racer_control::Point> local;
    for(auto point:points_) {auto shifted=inverse*tf2::Vector3(point.x,point.y,p.z);local.push_back({shifted.x(),shifted.y()});}
    // Remove traversed points, but retain the measured near section that the
    // camera can no longer see. Curved tracking can then use a shorter preview.
    size_t trim=0;
    while(trim<local.size() && local[trim].x<.06)++trim;
    local.erase(local.begin(),local.begin()+trim);
    points_.erase(points_.begin(),points_.begin()+trim);
    bool valid_path=!local.empty()&&racer_control::fresh(time,path_stamp_*1e-9,armed_?curve_memory_:path_age_);
    if(curve_align_) {
      // Rotate toward the last actually observed exit tangent, then require a
      // new camera path before translating again. This handles a tight smooth
      // bend that leaves the forward camera view, without extrapolating ink.
      auto candidate=racer_control::adaptive_pursuit(local,lookahead_,min_lookahead_,max_lookahead_,speed_,0.,max_yaw_,acceleration_);
      if(path_stamp_*1e-9>curve_align_stamp_ && valid_path && candidate.valid) {
        curve_align_=false;target_valid_=false;
      } else {
        if(time-curve_align_stamp_>5.) {error="curve_exit_not_reacquired";return {};}
        return {0.,std::clamp(1.3*racer_control::wrap(curve_exit_yaw_-yaw),-.30,.30),true};
      }
    }
    if(armed_) {
      bool exit_evidence=valid_path&&racer_control::fresh(time,path_stamp_*1e-9,path_age_)&&local.size()>8&&std::abs(local.front().y)<.10;
      if(exit_evidence) {
        auto a=local.front(),b=local.back();
        exit_evidence=std::abs(std::atan2(b.y-a.y,b.x-a.x))<.25 && racer_control::distance(a,b)>.20;
      }
      auto command=corner_.update(time,{p.x,p.y},yaw,odom_->twist.twist.linear.x,odom_->twist.twist.angular.z,
                                 exit_evidence,path_stamp_*1e-9,error);
      if(!error.empty())return {};
      if(corner_.active()||command.valid) {
        target_valid_=false;
        auto c=inverse*tf2::Vector3(corner_.corner.x,corner_.corner.y,p.z);
        command.target={c.x(),c.y()};
        return command;
      }
    }
    if(!valid_path) {error="path_timeout_or_invalid";return {};}
    racer_control::Point previous;
    if(target_valid_) {auto a=inverse*tf2::Vector3(target_.x,target_.y,p.z);previous={a.x(),a.y()};}
    auto command=racer_control::adaptive_pursuit(local,lookahead_,min_lookahead_,max_lookahead_,speed_,last_v_,max_yaw_,acceleration_,target_valid_?&previous:nullptr);
    const bool short_memory=path_stamp_*1e-9<time-path_age_ && local.size()>8 &&
        racer_control::distance(local.front(),local.back())<.20;
    if(!command.valid || short_memory) {
      if(armed_ && !corner_.active() && local.size()>8) {
        size_t before=local.size()-1;
        while(before>0 && racer_control::distance(local[before],local.back())<.06)--before;
        auto a=local[before],b=local.back();
        double heading=std::atan2(b.y-a.y,b.x-a.x);
        if(racer_control::distance(a,b)>.04 && std::abs(heading)>.25 && std::abs(heading)<1.8) {
          curve_align_=true;curve_align_stamp_=time;curve_exit_yaw_=yaw+heading;target_valid_=false;
          return {0.,std::clamp(1.3*heading,-.30,.30),true};
        }
      }
      if(!command.valid) {
        error="no_safe_ordered_lookahead";
      }
    }
    if(command.valid && armed_) {auto a=transform*tf2::Vector3(command.target.x,command.target.y,0);target_={a.x(),a.y()};target_valid_=true;}
    return command;
  }
  void debug(const racer_control::Command &command) {
    std::ostringstream out;
    out << "{\"state\":\"" << state_ << "\",\"observation_age\":" << now().seconds()-health_stamp_*1e-9
        << ",\"path_age\":" << now().seconds()-path_stamp_*1e-9 << ",\"lookahead\":" << command.lookahead
        << ",\"target\":[" << command.target.x << "," << command.target.y << "]"
        << ",\"corner_odom\":[" << corner_.corner.x << "," << corner_.corner.y << "]"
        << ",\"incoming_yaw_odom\":" << corner_.incoming_yaw << ",\"exit_yaw_odom\":" << corner_.exit_yaw << ",\"corner_age\":" << now().seconds()-corner_.memory_stamp
        << ",\"memory_distance\":" << corner_.traveled << ",\"memory_angle\":" << corner_.turned
        << ",\"cmd_v\":" << last_v_ << ",\"cmd_w\":" << last_w_ << "}";
    std_msgs::msg::String msg;msg.data=out.str();debug_pub_->publish(msg);
  }
  void tick() {
    // DDS image and TF streams can arrive out of order. Wait without blocking
    // the control timer; only a successfully transformed acquisition renews
    // freshness. Missing TF still expires the original image deadline.
    while(!pending_.empty()) {
      const auto &header=pending_.front()->path.header;const auto stamp=rclcpp::Time(header.stamp);
      if(!pending_.front()->image_valid || header.frame_id!=base_ ||
         !racer_control::fresh(now().seconds(),stamp.seconds(),path_age_) ||
         buffer_.canTransform(odom_frame_,base_,stamp,rclcpp::Duration::from_seconds(0))) {
        auto observation=pending_.front();pending_.pop_front();receive(*observation);
      } else break;
    }
    const double time = now().seconds();
    double dt = time-last_tick_; last_tick_ = time;
    if (dt < 0) { points_.clear(); odom_.reset(); path_stamp_ = seen_stamp_ = health_stamp_ = 0; pending_.clear(); stop("clock_reset"); }
    std::string error; auto desired = compute(error);
    if (!armed_) {
      if (state_.rfind("STOPPED", 0) != 0) state_ = desired.valid ? "READY" : "DISARMED: " + error;
      publish_zero(true); publish_state(); debug(desired); return;
    }
    if (!desired.valid) { stop(error); return; }
    if (dt <= 0) return;
    if (dt > .2) { stop("control_time_gap"); return; }
    last_v_ = racer_control::slew(last_v_, desired.v, acceleration_, dt);
    last_w_ = racer_control::slew(last_w_, desired.w, yaw_acceleration_, dt);
    state_=curve_align_?"CURVE_ALIGN":corner_.name(); publish_state();
    publish(last_v_, last_w_, true); debug(desired);
  }
  tf2_ros::Buffer buffer_; tf2_ros::TransformListener listener_;
  double curve_memory_, curve_align_stamp_=0., curve_exit_yaw_=0.;
  bool curve_align_=false;
  double speed_, lookahead_, max_yaw_, acceleration_, yaw_acceleration_, path_age_, odom_age_, wall_age_;
  double last_v_ = 0, last_w_ = 0, last_tick_ = 0;
  int64_t path_stamp_ = 0;
  bool armed_ = false;
  std::string base_, odom_frame_, state_ = "DISARMED";
  std::vector<racer_control::Point> points_;
  nav_msgs::msg::Odometry::ConstSharedPtr odom_;
  std::chrono::steady_clock::time_point path_wall_, odom_wall_;
  rclcpp::Subscription<racer_interfaces::msg::LineObservation>::SharedPtr observation_sub_;
  std::deque<racer_interfaces::msg::LineObservation::ConstSharedPtr> pending_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr debug_pub_;
  racer_control::CornerTurn corner_;
  racer_control::Point target_{0,0};
  bool target_valid_=false, image_valid_=false;
  int64_t seen_stamp_=0, health_stamp_=0;
  double min_lookahead_,max_lookahead_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr command_pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr state_pub_;
  rclcpp::Service<std_srvs::srv::SetBool>::SharedPtr enable_;
  rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char **argv) {
  rclcpp::init(argc, argv);
  try { rclcpp::spin(std::make_shared<LineController>()); }
  catch (const std::exception &e) { std::cerr << e.what() << '\n'; rclcpp::shutdown(); return 1; }
  rclcpp::shutdown(); return 0;
}
