#pragma once
#include "racer_control/line_tracker.hpp"
#include <fstream>
#include <sstream>
namespace racer_control {
struct Projection {double s=0, distance=1e9;Point point{}, tangent{};};
class LapRoute {
 public:
  std::vector<Point> points;std::vector<double> arc;
  explicit LapRoute(const std::string &file) {
    std::ifstream input(file);std::string line;
    if(!input)throw std::invalid_argument("Cannot open route");
    while(std::getline(input,line)) {
      if(line.empty()||line[0]=='#')continue;
      std::replace(line.begin(),line.end(),',',' ');std::istringstream row(line);Point p;
      if(!(row>>p.x>>p.y)||!std::isfinite(p.x)||!std::isfinite(p.y))throw std::invalid_argument("Invalid route row");
      if(!points.empty()&&(distance(p,points.back())<1e-6||distance(p,points.back())>.03))throw std::invalid_argument("Discontinuous route");
      arc.push_back(points.empty()?0:arc.back()+distance(p,points.back()));points.push_back(p);
    }
    if(points.size()<100||distance(points.front(),points.back())>.01)throw std::invalid_argument("Route must be a closed lap");
  }
  double length()const{return arc.back();}
  Point at(double s) const {
    s=std::clamp(s,0.,length());auto it=std::upper_bound(arc.begin(),arc.end(),s);
    size_t i=std::clamp(size_t(it-arc.begin()),size_t(1),points.size()-1);
    double t=(s-arc[i-1])/(arc[i]-arc[i-1]);return {points[i-1].x+t*(points[i].x-points[i-1].x),points[i-1].y+t*(points[i].y-points[i-1].y)};
  }
  Projection project(Point p,double lo,double hi) const {
    Projection out;
    size_t begin=std::max(size_t(1),size_t(std::lower_bound(arc.begin(),arc.end(),std::max(0.,lo))-arc.begin()));
    for(size_t i=begin;i<points.size()&&arc[i-1]<=hi;++i) {
      auto a=points[i-1],b=points[i];double l=arc[i]-arc[i-1];Point t{(b.x-a.x)/l,(b.y-a.y)/l};
      double f=std::clamp((p.x-a.x)*t.x+(p.y-a.y)*t.y,0.,l);Point q{a.x+f*t.x,a.y+f*t.y};
      double d=distance(p,q);if(d<out.distance)out={arc[i-1]+f,d,q,t};
    }return out;
  }
};
}
