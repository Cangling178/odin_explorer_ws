#include <cassert>
#include "../src/small_obstacle_filter.hpp"

int main()
{
  using Cloud = pcl::PointCloud<pcl::PointXYZ>;
  Cloud small;
  // Dense but low 5 x 22 cm patch, matching the observed near-body returns.
  for (int x = 0; x <= 5; ++x) {
    for (int y = 0; y <= 22; ++y) {
      small.push_back(pcl::PointXYZ(0.27f + x * 0.01f, y * 0.01f, 0.025f));
    }
  }
  auto filter = [](const Cloud & input) {
    return explorer_odin::filter_small_obstacles(input, 0.04, 0.25, 0.04);
  };
  assert(filter(small).empty());
  assert(filter(Cloud{}).empty());
  assert(explorer_odin::filter_small_obstacles(small, 0.04, 0.0, 0.04).size() == small.size());
  Cloud retained;
  // A narrow vertical obstacle, and a low but wide obstacle, must survive.
  for (int z = 0; z <= 30; ++z) {
    retained.push_back(pcl::PointXYZ(1.0f, 0.0f, 0.025f + z * 0.01f));
  }
  for (int y = 0; y <= 40; ++y) {
    retained.push_back(pcl::PointXYZ(2.0f, y * 0.01f, 0.025f));
  }
  Cloud mixed = small;
  mixed += retained;
  auto result = filter(mixed);
  assert(result.size() == retained.size());
  for (std::size_t i = 0; i < result.size(); ++i) {
    assert(result[i].x == retained[i].x && result[i].y == retained[i].y && result[i].z == retained[i].z);
  }
}
