// Offline graph extraction from a saved metric ground image; no ROS or truth.
#include "racer_perception/line_geometry.hpp"
#include <opencv2/imgcodecs.hpp>
#include <fstream>
#include <iostream>
int main(int argc,char **argv) {
  if(argc!=3 && argc!=5) {std::cerr<<"Usage: line_offline ground_gray.png output_prefix [near_x half_width]\n";return 2;}
  cv::Mat gray=cv::imread(argv[1],cv::IMREAD_GRAYSCALE);
  racer_perception::Grid grid;
  if(argc==5) {grid.near_x=std::stod(argv[3]);grid.half_width=std::stod(argv[4]);grid.validate();}
  if(gray.empty()||gray.rows!=grid.rows()||gray.cols!=grid.cols())return 2;
  cv::Mat visible(gray.size(),CV_8UC1,cv::Scalar(255));
  auto d=racer_perception::detect(gray,visible,grid,65,.008,.05,.10,.45);
  std::string prefix=argv[2];cv::imwrite(prefix+"_mask.png",d.mask);cv::imwrite(prefix+"_skeleton.png",d.skeleton);
  cv::Mat debug;cv::cvtColor(gray,debug,cv::COLOR_GRAY2BGR);
  auto pixel=[&](cv::Point2d p){return cv::Point(std::lround((grid.half_width-p.y)/grid.step),std::lround((p.x-grid.near_x)/grid.step));};
  std::ofstream report(prefix+".json");
  report<<"{\"valid\":"<<(d.valid()?"true":"false")<<",\"reason\":\""<<d.reason<<"\",\"corner_valid\":"<<(d.corner_valid?"true":"false")
        <<",\"corner\":["<<d.corner.x<<","<<d.corner.y<<"],\"exit\":["<<d.exit_direction.x<<","<<d.exit_direction.y<<"],\"path\":[";
  for(size_t i=0;i<d.points.size();++i) {auto p=d.points[i];if(i)report<<",";report<<"["<<p.x<<","<<p.y<<"]";cv::circle(debug,pixel(p),1,{0,0,255},-1);}
  report<<"]}\n";
  if(d.corner_valid) {cv::circle(debug,pixel(d.corner),4,{0,255,255},1);cv::arrowedLine(debug,pixel(d.corner),pixel(d.corner+d.exit_direction*.08),{0,255,0},1);}
  cv::imwrite(prefix+"_debug.png",debug);
  return d.valid()?0:1;
}
