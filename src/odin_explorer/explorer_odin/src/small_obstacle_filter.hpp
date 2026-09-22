#pragma once

#include <algorithm>
#include <limits>
#include <vector>
#include <pcl/common/common.h>
#include <pcl/common/io.h>
#include <pcl/point_types.h>
#include <pcl/search/kdtree.h>
#include <pcl/segmentation/extract_clusters.h>

namespace explorer_odin
{
// Input is already finite, height-cropped, and expressed in base_link.
// Remove only low, spatially small connected groups; keep tall narrow objects.
inline pcl::PointCloud<pcl::PointXYZ> filter_small_obstacles(
  const pcl::PointCloud<pcl::PointXYZ> & input, double tolerance,
  double max_extent, double max_z)
{
  using Cloud = pcl::PointCloud<pcl::PointXYZ>;
  if (input.empty() || max_extent <= 0.0) {return input;}
  auto cloud = input.makeShared();
  auto tree = pcl::search::KdTree<pcl::PointXYZ>::Ptr(new pcl::search::KdTree<pcl::PointXYZ>);
  tree->setInputCloud(cloud);
  pcl::EuclideanClusterExtraction<pcl::PointXYZ> extraction;
  extraction.setClusterTolerance(tolerance);
  extraction.setMinClusterSize(1);
  extraction.setMaxClusterSize(std::numeric_limits<int>::max());
  extraction.setSearchMethod(tree);
  extraction.setInputCloud(cloud);
  std::vector<pcl::PointIndices> clusters;
  extraction.extract(clusters);
  std::vector<int> keep;
  keep.reserve(input.size());
  for (const auto & cluster : clusters) {
    Eigen::Vector4f lower, upper;
    pcl::getMinMax3D(input, cluster.indices, lower, upper);
    const float extent = (upper - lower).head<3>().maxCoeff();
    if (extent <= max_extent && upper.z() <= max_z) {continue;}
    keep.insert(keep.end(), cluster.indices.begin(), cluster.indices.end());
  }
  // Preserve the input ordering as well as the original point coordinates.
  std::sort(keep.begin(), keep.end());
  Cloud output;
  pcl::copyPointCloud(input, keep, output);
  return output;
}
}  // namespace explorer_odin
