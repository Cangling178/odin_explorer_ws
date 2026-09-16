#include "racer_control/lap_route.hpp"
#include <rclcpp/rclcpp.hpp>
#include <racer_interfaces/msg/line_observation.hpp>
#include <nav_msgs/msg/odometry.hpp>
#include <geometry_msgs/msg/twist_stamped.hpp>
#include <std_msgs/msg/string.hpp>
#include <std_srvs/srv/set_bool.hpp>
#include <tf2_ros/buffer.h>
#include <tf2_ros/transform_listener.h>
#include <Eigen/Dense>
#include <sensor_msgs/msg/image.hpp>
#include "racer_perception/line_geometry.hpp"
#include <chrono>
#include <deque>
using racer_control::Point;
using racer_control::wrap;
class LapController:public rclcpp::Node {
 public:
  LapController():Node("lap_controller"),buffer_(get_clock()),listener_(buffer_) {
    cv::setNumThreads(1);
    route_=std::make_unique<racer_control::LapRoute>(declare_parameter("route_file",std::string{}));
    tx_=declare_parameter("start_x",route_->points.front().x);ty_=declare_parameter("start_y",route_->points.front().y);
    angle_=declare_parameter("start_yaw",-M_PI/2);
    grid_.near_x=declare_parameter("near_x",.10);
    grid_.far_x=declare_parameter("far_x",.75);
    grid_.half_width=declare_parameter("half_width",.50);
    grid_.step=declare_parameter("grid_step",.005);
    grid_.validate();
    speed_=declare_parameter("speed",.05);lookahead_=declare_parameter("lookahead",.10);
    if(!std::isfinite(speed_)||!std::isfinite(lookahead_)||!std::isfinite(tx_)||!std::isfinite(ty_)||!std::isfinite(angle_)||speed_<=0||speed_>.1||lookahead_<.06||lookahead_>.2)throw std::invalid_argument("Invalid lap limits");
    pub_=create_publisher<geometry_msgs::msg::TwistStamped>("cmd_vel",1);
    state_pub_=create_publisher<std_msgs::msg::String>("tracking_status",rclcpp::QoS(1).transient_local());
    debug_pub_=create_publisher<std_msgs::msg::String>("control_debug",1);
    odom_sub_=create_subscription<nav_msgs::msg::Odometry>("odom",rclcpp::SensorDataQoS(),[this](nav_msgs::msg::Odometry::ConstSharedPtr msg){
      auto p=msg->pose.pose.position;auto q=msg->pose.pose.orientation;
      double n=q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w;
      if(msg->header.frame_id!="odom"||msg->child_frame_id!="base_link"||!std::isfinite(p.x)||!std::isfinite(p.y)||!std::isfinite(n)||std::abs(n-1)>.01){stop("invalid_odom");return;}
      double stamp=rclcpp::Time(msg->header.stamp).seconds();
      if(racer_control::fresh(now().seconds(),stamp,.15)&&stamp>odom_stamp_){odom_=msg;odom_stamp_=stamp;odom_wall_=std::chrono::steady_clock::now();}
    });
    obs_sub_=create_subscription<racer_interfaces::msg::LineObservation>("observation",5,[this](racer_interfaces::msg::LineObservation::ConstSharedPtr msg){
      double stamp=rclcpp::Time(msg->path.header.stamp).seconds();
      if(stamp>seen_){pending_.push_back(msg);seen_=stamp;if(pending_.size()>5){pending_.clear();stop("observation_queue");}}
    });
    mask_sub_=create_subscription<sensor_msgs::msg::Image>("black_mask",3,[this](sensor_msgs::msg::Image::ConstSharedPtr m){masks_.push_back(m);if(masks_.size()>5)masks_.pop_front();});
    enable_=create_service<std_srvs::srv::SetBool>("~/enable",[this](const std_srvs::srv::SetBool::Request::SharedPtr req,std_srvs::srv::SetBool::Response::SharedPtr res){
      if(!req->data){armed_=false;state_="DISARMED";publish(0,0);res->success=true;}
      else if(ready()&&progress_<route_->length()-.05){armed_=true;state_="RUNNING";last_tick_=now().seconds();res->success=true;}
      else res->success=false;
      res->message=state_;status();
    });
    timer_=create_wall_timer(std::chrono::milliseconds(20),[this]{tick();});status();
  }
 private:
  Point world(Point p)const{return {tx_+std::cos(angle_)*p.x-std::sin(angle_)*p.y,ty_+std::sin(angle_)*p.x+std::cos(angle_)*p.y};}
  static double yaw(const geometry_msgs::msg::Quaternion &q){return std::atan2(2*(q.w*q.z+q.x*q.y),1-2*(q.y*q.y+q.z*q.z));}
  bool healthy()const {
    auto wall=std::chrono::steady_clock::now();double t=now().seconds();
    return odom_&&racer_control::fresh(t,odom_stamp_,.15)&&racer_control::fresh(t,health_stamp_,.35)&&
      std::chrono::duration<double>(wall-odom_wall_).count()<1&&std::chrono::duration<double>(wall-image_wall_).count()<1;
  }
  bool ready()const{return healthy()&&racer_control::fresh(now().seconds(),visual_stamp_,.35);}
  void status(){std_msgs::msg::String m;m.data=state_;state_pub_->publish(m);}
  void publish(double v,double w){geometry_msgs::msg::TwistStamped m;m.header.stamp=now();m.header.frame_id="base_link";m.twist.linear.x=v;m.twist.angular.z=w;pub_->publish(m);v_=v;w_=w;}
  void stop(std::string why){bool latch=armed_||state_.rfind("STOPPED",0)==0;armed_=false;state_=(latch?"STOPPED: ":"DISARMED: ")+why;publish(0,0);status();}
  void observe(const racer_interfaces::msg::LineObservation &msg) {
    double stamp=rclcpp::Time(msg.path.header.stamp).seconds();
    if(!msg.image_valid||msg.path.header.frame_id!="base_link"||!racer_control::fresh(now().seconds(),stamp,.35)){stop("invalid_image");return;}
    buffer_.lookupTransform("odom","base_link",msg.path.header.stamp);
    health_stamp_=stamp;image_wall_=std::chrono::steady_clock::now();
  }
  void align(const sensor_msgs::msg::Image &msg) {
    double stamp=rclcpp::Time(msg.header.stamp).seconds();
    if(msg.encoding!="mono8"||msg.width!=static_cast<unsigned>(grid_.cols())||msg.height!=static_cast<unsigned>(grid_.rows())||msg.step<msg.width||msg.data.size()<msg.step*msg.height)return;
    auto tf=buffer_.lookupTransform("odom","base_link",msg.header.stamp).transform;
    cv::Mat mask(msg.height,msg.width,CV_8UC1,const_cast<unsigned char*>(msg.data.data()),msg.step);
    cv::Mat dist;cv::distanceTransform(mask,dist,cv::DIST_L2,3);
    auto skeleton=racer_perception::thin(mask);
    std::vector<Point> observed;
    for(int r=0;r<skeleton.rows;++r)for(int c=0;c<skeleton.cols;++c)
      if(skeleton.at<unsigned char>(r,c)&&dist.at<float>(r,c)*2*grid_.step<=.05)
        {auto point=grid_.point(r,c);observed.push_back({point.x,point.y});}
    Point op{tf.translation.x,tf.translation.y};double oy=yaw(tf.rotation);
    // Localization matches all visible mapped ink, including previous loop limbs.
    // Only control progress uses an ordered window; clipping the localization
    // map to that window would misassociate visible crossing/loop geometry.
    // No Gazebo pose, overview camera, or evaluator feedback enters this node.
    Point base=world(op);double heading=angle_+oy;
    Eigen::Matrix3d a=Eigen::Matrix3d::Identity()*2.;Eigen::Vector3d b=Eigen::Vector3d::Zero();int count=0;double sum=0;
    for(size_t i=0;i<observed.size();i+=2){auto p=observed[i];
      if(!std::isfinite(p.x)||!std::isfinite(p.y)||std::hypot(p.x,p.y)>.90)continue;
      Point d{std::cos(heading)*p.x-std::sin(heading)*p.y,std::sin(heading)*p.x+std::cos(heading)*p.y};
      Point q{base.x+d.x,base.y+d.y};auto ref=route_->project(q,0,route_->length());
      if(ref.distance>.08)continue;
      // A 40 mm chord avoids fitting pixel staircases as a heading reference.
      auto l=route_->at(ref.s-.02),r=route_->at(ref.s+.02);double len=racer_control::distance(l,r);if(len<.015)continue;
      Point n{-(r.y-l.y)/len,(r.x-l.x)/len};double error=n.x*(ref.point.x-q.x)+n.y*(ref.point.y-q.y);
      Eigen::Vector3d j(n.x,n.y,-n.x*d.y+n.y*d.x);double weight=std::min(1.,.025/std::max(std::abs(error),1e-6));
      a+=weight*j*j.transpose();b+=weight*j*error;sum+=error*error;++count;
    }
    if(count<8||std::sqrt(sum/count)>.05)return;
    Eigen::Vector3d delta=a.ldlt().solve(b);if(!delta.allFinite())return;
    double da=std::clamp(delta[2],-.015,.015)*.25;
    Point desired{base.x+std::clamp(delta[0],-.012,.012)*.25,base.y+std::clamp(delta[1],-.012,.012)*.25};
    angle_+=da;auto shifted=world(op);tx_+=desired.x-shifted.x;ty_+=desired.y-shifted.y;
    visual_stamp_=stamp;visual_progress_=progress_;match_rms_=std::sqrt(sum/count);
  }
  void tick(){
    double t=now().seconds(),dt=t-last_tick_;last_tick_=t;
    if(dt<0){stop("clock_reset");return;}
    while(!pending_.empty()){
      auto msg=pending_.front();double stamp=rclcpp::Time(msg->path.header.stamp).seconds();
      if(!racer_control::fresh(t,stamp,.35)){pending_.pop_front();stop("observation_timeout");continue;}
      if(!buffer_.canTransform("odom","base_link",msg->path.header.stamp))break;
      pending_.pop_front();try{observe(*msg);}catch(const std::exception &){stop("observation_tf");}
    }
    while(!masks_.empty()) {
      auto mask=masks_.front();double stamp=rclcpp::Time(mask->header.stamp).seconds();
      if(stamp>health_stamp_)break;
      masks_.pop_front();
      if(!racer_control::fresh(t,stamp,.35)||!buffer_.canTransform("odom","base_link",mask->header.stamp))continue;
      try{align(*mask);}catch(const std::exception &){stop("alignment_transform");}
    }
    if(!armed_){if(state_.rfind("STOPPED",0)!=0&&state_!="FINISHED")state_=ready()?"READY":"DISARMED";publish(0,0);status();return;}
    if(!healthy()){stop("sensor_timeout");return;}
    if(dt<=0)return;
    if(dt>.2){stop("control_time_gap");return;}
    auto op=odom_->pose.pose.position;Point p=world({op.x,op.y});double heading=angle_+yaw(odom_->pose.pose.orientation);
    auto projection=route_->project(p,progress_-.08,progress_+.35);
    if(projection.distance>.12){stop("route_distance");return;}
    progress_=std::max(progress_,projection.s);
    if(progress_-visual_progress_>.65){stop("visual_alignment_distance");return;}
    if(progress_>route_->length()-.025&&racer_control::distance(p,route_->points.front())<.065){armed_=false;state_="FINISHED";publish(0,0);status();return;}
    Point target=route_->at(std::min(route_->length(),progress_+lookahead_));
    double dx=target.x-p.x,dy=target.y-p.y;double local_y=-std::sin(heading)*dx+std::cos(heading)*dy;
    double k=2*local_y/std::max(dx*dx+dy*dy,.0025);
    double desired_v=std::min(speed_,.45/std::max(std::abs(k),1e-6));
    if(desired_v<.006){stop("continuous_turn_infeasible");return;}
    double desired_w=desired_v*k;
    double v=racer_control::slew(v_,desired_v,.10,dt),w=racer_control::slew(w_,desired_w,.8,dt);
    publish(v,w);state_="RUNNING";status();
    std_msgs::msg::String debug;std::ostringstream out;
    out<<"{\"progress\":"<<progress_<<",\"length\":"<<route_->length()<<",\"x\":"<<p.x<<",\"y\":"<<p.y<<",\"yaw\":"<<heading<<",\"error\":"<<projection.distance<<",\"observation_age\":"<<t-health_stamp_<<",\"visual_age\":"<<t-visual_stamp_<<",\"match_rms\":"<<match_rms_<<",\"v\":"<<v<<",\"w\":"<<w<<"}";
    debug.data=out.str();debug_pub_->publish(debug);
  }
  racer_perception::Grid grid_;
  std::unique_ptr<racer_control::LapRoute> route_;tf2_ros::Buffer buffer_;tf2_ros::TransformListener listener_;
  double tx_,ty_,angle_,speed_,lookahead_,progress_=0,visual_progress_=0,visual_stamp_=0,match_rms_=0,seen_=0,health_stamp_=0,odom_stamp_=0,last_tick_=0,v_=0,w_=0;
  bool armed_=false;std::string state_="DISARMED";
  std::chrono::steady_clock::time_point image_wall_,odom_wall_;
  nav_msgs::msg::Odometry::ConstSharedPtr odom_;
  std::deque<racer_interfaces::msg::LineObservation::ConstSharedPtr> pending_;
  std::deque<sensor_msgs::msg::Image::ConstSharedPtr> masks_;
  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr mask_sub_;
  rclcpp::Subscription<nav_msgs::msg::Odometry>::SharedPtr odom_sub_;
  rclcpp::Subscription<racer_interfaces::msg::LineObservation>::SharedPtr obs_sub_;
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_;
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr state_pub_,debug_pub_;
  rclcpp::Service<std_srvs::srv::SetBool>::SharedPtr enable_;rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc,char **argv){rclcpp::init(argc,argv);try{rclcpp::spin(std::make_shared<LapController>());}catch(const std::exception &e){std::cerr<<e.what()<<'\n';return 1;}rclcpp::shutdown();return 0;}
