#pragma once
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

namespace racer_control {
struct Point { double x, y; };
struct Command { double v = 0, w = 0; bool valid = false; Point target{0,0}; double lookahead=0, target_s=0; };
inline bool fresh(double now, double stamp, double limit) {
  return std::isfinite(now) && std::isfinite(stamp) && stamp > 0 && now-stamp >= -.02 && now-stamp <= limit;
}
inline Command pursuit(const std::vector<Point> &path, double lookahead, double speed, double max_yaw) {
  if (path.size() < 2 || !std::isfinite(lookahead) || lookahead <= 0 ||
      !std::isfinite(speed) || speed <= 0 || !std::isfinite(max_yaw) || max_yaw <= 0) return {};
  for (auto p : path) if (!std::isfinite(p.x) || !std::isfinite(p.y)) return {};
  // Select the first forward segment crossing the lookahead circle. Refuse a
  // short path instead of pursuing its endpoint indefinitely after losing line.
  for (size_t i = 1; i < path.size(); ++i) {
    auto a = path[i-1], b = path[i];
    const double dx = b.x-a.x, dy = b.y-a.y;
    const double aa = dx*dx+dy*dy, bb = 2*(a.x*dx+a.y*dy);
    const double cc = a.x*a.x+a.y*a.y-lookahead*lookahead;
    const double disc = bb*bb-4*aa*cc;
    if (aa < 1e-12 || disc < 0) continue;
    double t = (-bb+std::sqrt(disc))/(2*aa);
    // Adjacent segments share their endpoints. Roundoff must not reject the
    // same real crossing as t>1 on one and t<0 on the next (a centered line).
    if (t < -1e-9 || t > 1+1e-9) continue;
    t = std::clamp(t,0.,1.);
    const Point target{a.x+t*dx, a.y+t*dy};
    if (target.x <= .05) continue;
    double curvature = 2*target.y/(lookahead*lookahead);
    double v = std::min(speed, max_yaw/std::max(std::abs(curvature), 1e-9));
    return {v, v*curvature, true, target, lookahead, 0};
  }
  return {};
}
inline double slew(double previous, double desired, double rate, double dt) {
  return previous + std::clamp(desired-previous, -rate*dt, rate*dt);
}

inline double distance(Point a, Point b) { return std::hypot(a.x-b.x,a.y-b.y); }
inline double wrap(double a) { return std::atan2(std::sin(a),std::cos(a)); }
inline bool ordered_path(const std::vector<Point> &path) {
  if(path.size()<2 || path.size()>2000)return false;
  double length=0;
  for(size_t i=0;i<path.size();++i) {
    auto p=path[i];
    if(!std::isfinite(p.x)||!std::isfinite(p.y)||std::abs(p.x)>3||std::abs(p.y)>2)return false;
    if(i) {double d=distance(p,path[i-1]);if(d<.0001||d>.12)return false;length+=d;}
  }
  return length>=.08 && length<5;
}
// Retain already observed near-ground points as they enter the camera blind
// zone. Join only overlapping observations in odometry; never fill a line gap.
inline std::vector<Point> merge_observed_path(const std::vector<Point> &old,
                                             const std::vector<Point> &observed, bool *accepted=nullptr) {
  if(accepted)*accepted=true;
  if(old.empty() || observed.empty())return observed;
  auto closest=[&](Point p) {
    size_t index=0;
    for(size_t i=1;i<old.size();++i)if(distance(old[i],p)<distance(old[index],p))index=i;
    return index;
  };
  size_t first=closest(observed.front()),last=closest(observed.back());
  if(distance(old[first],observed.front())>.035) {
    if(accepted)*accepted=false;
    return old;
  }
  std::vector<Point> merged(old.begin(),old.begin()+first);
  for(auto p:observed)if(merged.empty()||distance(p,merged.back())>=.001)merged.push_back(p);
  // Preserve an occluded suffix only at a close overlap, and never carry a
  // disconnected old fragment into the new path.
  if(last>=first && distance(old[last],observed.back())<.01) {
    for(size_t i=last+1;i<old.size();++i) {
      double gap=distance(old[i],merged.back());
      if(gap>.02)break;
      if(gap>=.001)merged.push_back(old[i]);
    }
  }
  return merged;
}
inline Command adaptive_pursuit(const std::vector<Point> &path, double nominal, double min_lookahead,
    double max_lookahead, double speed, double previous_speed, double max_yaw, double acceleration,
    const Point *previous_target=nullptr) {
  if(!ordered_path(path))return {};
  std::vector<double> arc(path.size(),0);
  for(size_t i=1;i<path.size();++i)arc[i]=arc[i-1]+distance(path[i],path[i-1]);
  double curvature=0;
  // Chords over 80 mm suppress skeleton pixel staircase curvature.
  for(size_t i=1;i+1<path.size();++i) {
    if(arc[i]<.08)continue;
    auto l=std::lower_bound(arc.begin(),arc.end(),arc[i]-.08);
    auto r=std::lower_bound(arc.begin(),arc.end(),arc[i]+.08);
    if(r==arc.end())break;
    auto a=path[l-arc.begin()],b=path[i],c=path[r-arc.begin()];
    if(distance(a,b)<.04 || distance(b,c)<.04)continue;
    double turn=std::abs(wrap(std::atan2(c.y-b.y,c.x-b.x)-std::atan2(b.y-a.y,b.x-a.x)));
    curvature=std::max(curvature,turn/.08);
  }
  double reach=0;for(auto p:path)reach=std::max(reach,std::hypot(p.x,p.y));
  double lookahead=std::clamp(nominal+(previous_speed-speed)*1.0-.055*curvature,min_lookahead,max_lookahead);
  lookahead=std::max(lookahead,std::hypot(path.front().x,path.front().y)+.025);
  if(lookahead>max_lookahead)return {};
  lookahead=std::min(lookahead,reach-.025);
  if(lookahead<min_lookahead)return {};
  const double available=std::max(0.,arc.back()-.04);
  const double limited=std::min({speed,max_yaw/std::max(curvature,1e-6),std::sqrt(2*acceleration*available),speed*std::min(1.,arc.back()/.20)});
  if(limited<.005)return {};
  auto command=pursuit(path,lookahead,limited,max_yaw);
  if(!command.valid)return {};
  // Project both targets onto this acquisition's arc coordinate; a new frame
  // can extend the visible path but cannot authorize a jump to another S limb.
  auto coordinate=[&](Point target) {
    double best=1e9,result=0;
    for(size_t i=1;i<path.size();++i) {
      auto a=path[i-1],b=path[i];double dx=b.x-a.x,dy=b.y-a.y;
      double t=std::clamp(((target.x-a.x)*dx+(target.y-a.y)*dy)/(dx*dx+dy*dy),0.,1.);
      double d=distance(target,{a.x+t*dx,a.y+t*dy});
      if(d<best) {best=d;result=arc[i-1]+t*(arc[i]-arc[i-1]);}
    }
    return result;
  };
  command.target_s=coordinate(command.target);
  if(previous_target && (std::abs(command.target_s-coordinate(*previous_target))>.12 || distance(command.target,*previous_target)>.15))return {};
  return command;
}

struct CornerConfig {
  double memory_time=18., memory_distance=.45, memory_angle=1.9;
  double approach_speed=.04, turn_rate=.30, stop_distance=.080;
};
// Coordinates in wheel odometry, never in the fixture or Gazebo truth frame.
class CornerTurn {
 public:
  enum class Phase { TRACK, APPROACH, STOP, TURN, REACQUIRE };
  Phase phase=Phase::TRACK;
  CornerConfig config;
  Point corner{0,0}; double exit_yaw=0, incoming_yaw=0;
  int stable=0;
  bool consumed=false;
  double memory_stamp=0, phase_stamp=0, traveled=0, turned=0;
  Point memory_pose{0,0}, last_pose{0,0};double last_yaw=0;
  void reset() { auto saved=config; *this=CornerTurn(); config=saved; }
  const char *name() const {
    switch(phase) {case Phase::TRACK:return "RUNNING";case Phase::APPROACH:return "APPROACH";
      case Phase::STOP:return "CORNER_STOP";case Phase::TURN:return "TURN";default:return "REACQUIRE";}
  }
  void observe(double stamp, Point observed, double outgoing, double incoming, Point pose, double yaw) {
    if(consumed || phase==Phase::STOP || phase==Phase::TURN || phase==Phase::REACQUIRE)return;
    bool consistent=stable>0 && stamp-memory_stamp<.35 && distance(observed,corner)<.025 &&
                    std::abs(wrap(outgoing-exit_yaw))<.18 && std::abs(wrap(incoming-incoming_yaw))<.18;
    if(phase==Phase::APPROACH && !consistent)return;
    stable=consistent?stable+1:1;
    if(consistent) {
      corner={.7*corner.x+.3*observed.x,.7*corner.y+.3*observed.y};
      exit_yaw+=.25*wrap(outgoing-exit_yaw);incoming_yaw+=.25*wrap(incoming-incoming_yaw);
    } else {corner=observed;exit_yaw=outgoing;incoming_yaw=incoming;}
    memory_stamp=stamp;
    memory_pose=last_pose=pose;last_yaw=yaw;traveled=turned=0;
  }
  void no_corner(double stamp) { if(phase==Phase::TRACK && stamp-memory_stamp>.35)stable=0; }
  bool active() const {return phase!=Phase::TRACK;}
  Command update(double time, Point pose, double yaw, double measured_v, double measured_w,
                 bool fresh_exit, double exit_stamp, std::string &error) {
    if(phase==Phase::TRACK) {
      if(consumed||stable<3||time-memory_stamp>.35||distance(corner,pose)>.60)return {};
      phase=Phase::APPROACH;phase_stamp=time;
    }
    traveled+=distance(pose,last_pose);turned+=std::abs(wrap(yaw-last_yaw));last_pose=pose;last_yaw=yaw;
    if(time-memory_stamp>config.memory_time||traveled>config.memory_distance||turned>config.memory_angle) {
      error="corner_memory_limit";return {};
    }
    double dx=corner.x-pose.x,dy=corner.y-pose.y;
    double forward=dx*std::cos(incoming_yaw)+dy*std::sin(incoming_yaw);
    double lateral=-dx*std::sin(incoming_yaw)+dy*std::cos(incoming_yaw);
    if(phase==Phase::APPROACH) {
      if(std::abs(lateral)>.07||forward<-.025) {error="corner_position_uncertain";return {};}
      if(forward<=config.stop_distance) {phase=Phase::STOP;phase_stamp=time;return {0,0,true};}
      double v=std::min(config.approach_speed,std::sqrt(2*.08*std::max(0.,forward-config.stop_distance)));
      double w=std::clamp(1.5*wrap(incoming_yaw-yaw)+4.0*lateral,-.25,.25);
      return {v,w,true,corner};
    }
    if(phase==Phase::STOP) {
      if(time-phase_stamp>2.) {error="corner_failed_to_stop";return {};}
      if(time-phase_stamp>.3&&std::abs(measured_v)<.005&&std::abs(measured_w)<.02) {
        phase=Phase::TURN;phase_stamp=time;
      }
      return {0,0,true};
    }
    double heading=wrap(exit_yaw-yaw);
    if(phase==Phase::TURN) {
      if(std::abs(heading)<.10) {phase=Phase::REACQUIRE;phase_stamp=time;reacquired_=0;}
      return {0,std::clamp(1.3*heading,-config.turn_rate,config.turn_rate),true};
    }
    // Zero translation until actual camera exit evidence has been accepted on
    // multiple different acquisition stamps by the caller. Yaw alone is not completion.
    if(fresh_exit && std::abs(heading)<.12) {
      if(exit_stamp>last_exit_stamp_) {++reacquired_;last_exit_stamp_=exit_stamp;}
    } else reacquired_=0;
    if(reacquired_>=3) {phase=Phase::TRACK;consumed=true;stable=0;return {0,0,true};}
    if(time-phase_stamp>2.5) {error="exit_not_reacquired";return {};}
    return {0,std::clamp(heading,-.15,.15),true};
  }
 private:
  int reacquired_=0;double last_exit_stamp_=0;
};
}  // namespace racer_control
