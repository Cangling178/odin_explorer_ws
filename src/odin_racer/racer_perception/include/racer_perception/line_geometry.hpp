#pragma once
#include <opencv2/core.hpp>
#include <opencv2/imgproc.hpp>
#include <array>
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <string>
#include <vector>

namespace racer_perception {
// 正向多项式与斜切参数约定与 racer_description/fishpoly.py 保持一致。
// 地面网格重投影只需正向相机模型，无需求镜头逆变换。
struct FishPoly {
  std::array<double, 9> k;
  std::vector<double> d;
  void validate() const {
    if (d.size() != 6)
      throw std::invalid_argument("Expected six FishPoly coefficients");
    for (double v : k)
      if (!std::isfinite(v))
        throw std::invalid_argument("Nonfinite K");
    for (double v : d)
      if (!std::isfinite(v))
        throw std::invalid_argument("Nonfinite D");
    if (k[0] <= 0 || k[4] <= 0 || k[3] != 0 || k[6] != 0 || k[7] != 0 || k[8] != 1)
      throw std::invalid_argument("Invalid FishPoly K");
  }
  cv::Point2d project(const cv::Vec3d &p) const {
    if (!std::isfinite(p[0]) || !std::isfinite(p[1]) || !std::isfinite(p[2]) || p[2] <= 0)
      return {-1, -1};
    const double r = std::hypot(p[0], p[1]), theta = std::atan2(r, p[2]);
    double poly = d[5];
    for (int i = 4; i >= 0; --i)
      poly = d[i] + theta * poly;
    const double scale = r > 1e-12 ? theta * (1 + theta * poly) / r : 0;
    return {k[0] * scale * p[0] + k[1] * scale * p[1] + k[2], k[4] * scale * p[1] + k[5]};
  }
};

// 车体地面网格：x 向前、y 向左，长度单位 m；行增大对应前方，列增大对应右侧。
struct Grid {
  double near_x = .25, far_x = .75, half_width = .30, step = .005, ground_z = -.03325;
  int rows() const {
    return static_cast<int>(std::round((far_x - near_x) / step)) + 1;
  }
  int cols() const {
    return static_cast<int>(std::round(2 * half_width / step)) + 1;
  }
  cv::Point2d point(int row, double col) const {
    return {near_x + row * step, half_width - col * step};
  }

  void validate() const {
    for (double v : {near_x, far_x, half_width, step, ground_z})
      if (!std::isfinite(v))
        throw std::invalid_argument("Nonfinite ground grid");
    if (near_x <= 0 || far_x <= near_x || half_width <= 0 || step < .001 || far_x > 3 ||
        half_width > 2 || rows() > 2000 || cols() > 2000)
      throw std::invalid_argument("Invalid ground grid");
  }
};

// points 为有序实测路径；reason 描述整体有效性，end_reason 描述追踪终止原因。
struct Detection {
  std::vector<cv::Point2d> points;
  cv::Mat mask, skeleton;
  cv::Point2d corner, exit_direction;
  bool corner_valid = false;
  unsigned exits = 0;
  double confidence = 0;
  std::string reason = "no_line", end_reason = "grid_end";
  bool valid() const {
    return reason == "valid";
  }
};

// 上一帧种子经运动补偿后的点和方向，用于约束本帧起点搜索。
struct SeedHint {
  cv::Point2d point, direction{1, 0};
  bool valid = false;
};

// Zhang-Suen 细化保留骨架连通性及侧向出口。
// 图像边缘补零，不在不可见像素之间人为连线。
inline cv::Mat thin(const cv::Mat &mask) {
  cv::Mat work;
  cv::copyMakeBorder(mask, work, 1, 1, 1, 1, cv::BORDER_CONSTANT, 0);
  work /= 255;
  bool changed;
  do {
    changed = false;
    for (int pass = 0; pass < 2; ++pass) {
      std::vector<cv::Point> remove;
      for (int r = 1; r < work.rows - 1; ++r)
        for (int c = 1; c < work.cols - 1; ++c) {
          if (!work.at<uchar>(r, c))
            continue;
          int p[9] = {work.at<uchar>(r - 1, c),
                      work.at<uchar>(r - 1, c + 1),
                      work.at<uchar>(r, c + 1),
                      work.at<uchar>(r + 1, c + 1),
                      work.at<uchar>(r + 1, c),
                      work.at<uchar>(r + 1, c - 1),
                      work.at<uchar>(r, c - 1),
                      work.at<uchar>(r - 1, c - 1),
                      work.at<uchar>(r - 1, c)};
          int n = 0, a = 0;
          for (int i = 0; i < 8; ++i) {
            n += p[i];
            a += p[i] == 0 && p[i + 1] != 0;
          }
          if (n < 2 || n > 6 || a != 1)
            continue;
          bool allowed = pass == 0 ? p[0] * p[2] * p[4] == 0 && p[2] * p[4] * p[6] == 0
                                   : p[0] * p[2] * p[6] == 0 && p[0] * p[4] * p[6] == 0;
          if (allowed)
            remove.emplace_back(c, r);
        }
      for (auto p : remove)
        work.at<uchar>(p) = 0;
      changed |= !remove.empty();
    }
  } while (changed);
  return work(cv::Rect(1, 1, mask.cols, mask.rows)).clone() * 255;
}

// 流程：阈值分割 → 细化/去毛刺 → 种子与连通性检查 → 有序追踪 → 弯角与置信度。
inline Detection detect(const cv::Mat &gray,
                        const cv::Mat &visible,
                        const Grid &grid,
                        double threshold,
                        double min_width,
                        double max_width,
                        double min_length,
                        double seed_limit,
                        SeedHint hint = {}) {
  Detection result;
  cv::compare(gray, threshold, result.mask, cv::CMP_LT);
  cv::bitwise_and(result.mask, visible, result.mask);
  // 使用与方向无关的局部厚度排除宽色块，不能用水平像素跨度判断，
  // 因为真正的直角弯出口本身就可能沿水平方向延伸。
  cv::Mat distance;
  cv::distanceTransform(result.mask, distance, cv::DIST_L2, 3);
  result.skeleton = thin(result.mask);
  // 先移除厚区域的骨架，再选择连通分量和种子，避免把场外暗地面
  // 或车身阴影当成近端线路；真实窄分叉保留交汇点，仍会被判为歧义。
  result.skeleton.setTo(0, distance > max_width / (2 * grid.step));
  const int rows = gray.rows, cols = gray.cols, total = rows * cols;
  auto neighbors = [&](int id) {
    std::vector<int> out;
    int r = id / cols, c = id % cols;
    for (int dr = -1; dr <= 1; ++dr)
      for (int dc = -1; dc <= 1; ++dc) {
        int nr = r + dr, nc = c + dc;
        if ((!dr && !dc) || nr < 0 || nr >= rows || nc < 0 || nc >= cols ||
            !result.skeleton.at<uchar>(nr, nc))
          continue;
        // 已有正交连接时不再添加对角边，避免形成多余的三角连接。
        if (dr && dc && (result.skeleton.at<uchar>(r, nc) || result.skeleton.at<uchar>(nr, c)))
          continue;
        out.push_back(nr * cols + nc);
      }
    return out;
  };
  auto edge = [&](int id) {
    int r = id / cols, c = id % cols;
    return r < 3 || r >= rows - 3 || c < 3 || c >= cols - 3;
  };

  // 只剪除接在交汇点上的短毛刺，保留边界出口；
  // 孤立短线段交给后续长度检查判定。
  for (int iteration = 0; iteration < 3; ++iteration) {
    std::vector<int> remove;
    for (int id = 0; id < total; ++id) {
      if (!result.skeleton.at<uchar>(id / cols, id % cols) || edge(id) || neighbors(id).size() != 1)
        continue;
      std::vector<int> branch{id};
      int previous = -1, current = id;
      for (int step = 0; step < 6; ++step) {
        auto next = neighbors(current);
        next.erase(std::remove(next.begin(), next.end(), previous), next.end());
        if (next.size() != 1)
          break;
        previous = current;
        current = next[0];
        if (neighbors(current).size() > 2) {
          remove.insert(remove.end(), branch.begin(), branch.end());
          break;
        }
        if (edge(current))
          break;
        branch.push_back(current);
      }
    }
    for (int id : remove)
      result.skeleton.at<uchar>(id / cols, id % cols) = 0;
  }

  // 选择车前近端的唯一连通分量；若存在多个合理种子则判为歧义，
  // 不能仅因为某条线更靠近图像中心就选中它。
  std::vector<int> candidates;
  for (int r = 0; r < std::min(rows, static_cast<int>((.40 - grid.near_x) / grid.step) + 1); ++r)
    for (int c = 2; c < cols - 2; ++c) {
      if (!result.skeleton.at<uchar>(r, c))
        continue;
      auto p = grid.point(r, c);
      if (std::abs(p.y) > seed_limit || (hint.valid && cv::norm(p - hint.point) > .10))
        continue;
      candidates.push_back(r * cols + c);
    }
  if (candidates.empty()) {
    result.reason = "no_near_seed";
    return result;
  }
  std::vector<int> component(total, -1);
  int count = 0;
  for (int seed : candidates)
    if (component[seed] < 0) {
      std::vector<int> queue{seed};
      component[seed] = count;
      for (size_t i = 0; i < queue.size(); ++i)
        for (int n : neighbors(queue[i]))
          if (component[n] < 0) {
            component[n] = count;
            queue.push_back(n);
          }
      ++count;
    }
  if (count != 1) {
    // 多个被裁切的侧向片段不一定代表多条前向路线；
    // 方向或长度证据不足时返回失败，不任意选取分支。
    unsigned routes = 0;
    for (int label = 0; label < count; ++label) {
      int near = rows, far = -1;
      for (int id = 0; id < total; ++id)
        if (component[id] == label) {
          near = std::min(near, id / cols);
          far = std::max(far, id / cols);
        }
      if ((far - near) * grid.step >= .10)
        ++routes;
    }
    result.reason = routes >= 2 ? "ambiguous_branches" : "insufficient_visible_length";
    result.exits = routes >= 2 ? routes : 0;
    return result;
  }
  int seed = candidates.front();
  double best = 1e9;
  for (int id : candidates) {
    auto p = grid.point(id / cols, id % cols);
    double score = hint.valid ? cv::norm(p - hint.point) : p.x - grid.near_x + .1 * std::abs(p.y);
    if (score < best) {
      best = score;
      seed = id;
    }
  }
  int previous = -1, current = seed;
  std::vector<bool> visited(total, false);
  cv::Point2d direction = hint.valid ? hint.direction : cv::Point2d(1, 0);
  double length = 0;
  while (!visited[current]) {
    visited[current] = true;
    int r = current / cols, c = current % cols;
    auto p = grid.point(r, c);
    if (2 * distance.at<float>(r, c) * grid.step > max_width) {
      result.end_reason = "broad_line_or_crossing";
      break;
    }
    // 单像素毛刺已被剪除；持续过细的线路由后续平均置信度过滤，
    // 避免逐点截断破坏弯角连通性。
    if (!result.points.empty())
      length += cv::norm(p - result.points.back());
    result.points.push_back(p);
    auto next = neighbors(current);
    next.erase(std::remove(next.begin(), next.end(), previous), next.end());
    if (previous < 0) {
      next.erase(std::remove_if(next.begin(),
                                next.end(),
                                [&](int first) {
                                  int prior = current, node = first;
                                  std::vector<int> seen{current};
                                  double support = 0;
                                  while (support < .04 &&
                                         std::find(seen.begin(), seen.end(), node) == seen.end()) {
                                    support += cv::norm(grid.point(node / cols, node % cols) -
                                                        grid.point(prior / cols, prior % cols));
                                    seen.push_back(node);
                                    auto onward = neighbors(node);
                                    onward.erase(std::remove(onward.begin(), onward.end(), prior),
                                                 onward.end());
                                    if (onward.size() != 1)
                                      break;
                                    prior = node;
                                    node = onward[0];
                                  }
                                  auto chord = grid.point(node / cols, node % cols) - p;
                                  // 像素阶梯的第一条边可能垂直于真实切线；
                                  // 使用具有实际长度的弦判断前进方向，不只看单个像素边。
                                  return chord.dot(direction) <= .20 * cv::norm(chord);
                                }),
                 next.end());
    }
    if (previous < 0 && next.size() > 1 && neighbors(current).size() == 2) {
      result.reason = "insufficient_visible_length";
      return result;
    }
    if (next.empty())
      break;
    if (next.size() > 1) {
      unsigned supported = 0;
      for (int first : next) {
        int prior = current, node = first;
        double support = 0;
        std::vector<int> seen{current};
        while (support < .04 && std::find(seen.begin(), seen.end(), node) == seen.end()) {
          support += cv::norm(grid.point(node / cols, node % cols) -
                              grid.point(prior / cols, prior % cols));
          seen.push_back(node);
          auto onward = neighbors(node);
          onward.erase(std::remove(onward.begin(), onward.end(), prior), onward.end());
          if (onward.size() != 1)
            break;
          prior = node;
          node = onward[0];
        }
        if (support >= .04)
          ++supported;
      }
      result.end_reason = supported >= 2 ? "ambiguous_branches" : "insufficient_visible_length";
      result.exits = supported >= 2 ? supported : 0;
      double removed = 0;
      while (result.points.size() > 1 && removed < .025) {
        double d = cv::norm(result.points.back() - result.points[result.points.size() - 2]);
        removed += d;
        length -= d;
        result.points.pop_back();
      }
      break;
    }
    previous = current;
    current = next[0];
  }
  if (result.points.size() < 2 || length < min_length) {
    result.reason =
        result.end_reason == "grid_end" ? "insufficient_visible_length" : result.end_reason;
    return result;
  }

  // 在弯角两侧各取约 65 mm 的支撑段，检测持续的方向变化。
  // 保留原始有序路径点，不用跨弯直线平滑掉拐角。
  std::vector<double> arc(result.points.size(), 0);
  for (size_t i = 1; i < arc.size(); ++i)
    arc[i] = arc[i - 1] + cv::norm(result.points[i] - result.points[i - 1]);
  double strongest = 0;
  for (size_t i = 1; i + 1 < arc.size(); ++i) {
    auto l = std::lower_bound(arc.begin(), arc.end(), arc[i] - .065);
    auto r = std::lower_bound(arc.begin(), arc.end(), arc[i] + .065);
    if (arc[i] < .065 || r == arc.end())
      continue;
    auto a = result.points[i] - result.points[l - arc.begin()];
    auto b = result.points[r - arc.begin()] - result.points[i];
    double angle = std::atan2(a.x * b.y - a.y * b.x, a.dot(b));
    if (std::abs(angle) > 1.05 && std::abs(angle) > strongest) {
      strongest = std::abs(angle);
      result.corner = result.points[i];
      result.exit_direction = b / cv::norm(b);
      result.corner_valid = true;
    }
  }

  double width_sum = 0;
  for (auto p : result.points)
    width_sum += 2 *
                 distance.at<float>(std::lround((p.x - grid.near_x) / grid.step),
                                    std::lround((grid.half_width - p.y) / grid.step)) *
                 grid.step;
  result.confidence = std::min(1., length / (2 * min_length)) *
                      std::min(1., width_sum / result.points.size() / min_width);
  result.reason = "valid";
  if (result.exits == 0)
    result.exits = 1;
  return result;
}
}  // namespace racer_perception
