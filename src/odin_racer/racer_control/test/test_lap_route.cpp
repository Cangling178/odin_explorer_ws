#include "racer_control/lap_route.hpp"
#include <gtest/gtest.h>
#include <unistd.h>
#include <cstdio>
using racer_control::LapRoute;
class LapRouteTest : public ::testing::Test {
 protected:
  std::string file;
  void SetUp() override {
    char name[] = "/tmp/racer_lap_XXXXXX";
    int fd = mkstemp(name);
    ASSERT_GE(fd, 0);
    close(fd);
    file = name;
    std::ofstream out(file);
    // 八字路线两次经过同一交叉点，但对应不同的累计弧长。
    std::vector<racer_control::Point> corners = {
        {0, 0}, {1, 1}, {0, 2}, {-1, 1}, {0, 0}, {1, -1}, {0, -2}, {-1, -1}, {0, 0}};
    for (size_t i = 1; i < corners.size(); ++i)
      for (int j = 0; j < 100; ++j) {
        double t = j / 100.;
        out << corners[i - 1].x + t * (corners[i].x - corners[i - 1].x) << ","
            << corners[i - 1].y + t * (corners[i].y - corners[i - 1].y) << "\n";
      }
    out << "0,0\n";
  }

  void TearDown() override {
    std::remove(file.c_str());
  }
};

TEST_F(LapRouteTest, CrossingKeepsOrderedVisit) {
  LapRoute route(file);
  auto first = route.project({.001, .001}, 0, .3);
  auto second = route.project({.001, .001}, 5.3, 6.0);
  EXPECT_LT(first.s, .02);
  EXPECT_NEAR(second.s, 4 * std::sqrt(2), .01);
}

TEST_F(LapRouteTest, SamplesAndEndpointAreBounded) {
  LapRoute route(file);
  EXPECT_NEAR(route.length(), 8 * std::sqrt(2), .001);
  EXPECT_NEAR(route.at(.5 * std::sqrt(2)).x, .5, .001);
  EXPECT_DOUBLE_EQ(route.at(-1).x, 0);
  EXPECT_NEAR(route.at(100).y, 0, 1e-9);
}

TEST_F(LapRouteTest, RejectsDisconnectedAndNonfiniteRoute) {
  {
    std::ofstream out(file);
    out << "0,0\n1,1\n";
  }
  EXPECT_THROW(LapRoute route(file), std::invalid_argument);
  {
    std::ofstream out(file);
    out << "nan,0\n";
  }
  EXPECT_THROW(LapRoute route(file), std::invalid_argument);
}

TEST_F(LapRouteTest, MissingFileFails) {
  EXPECT_THROW(LapRoute route(file + "missing"), std::invalid_argument);
}

TEST_F(LapRouteTest, LocalizationCanMatchVisibleInkOutsideDrivingWindow) {
  LapRoute route(file);
  auto ink = route.at(4.8);
  auto full = route.project(ink, 0, route.length());
  auto forward = route.project(ink, 5.6, 7.1);
  EXPECT_LT(full.distance, 1e-6);
  EXPECT_GT(forward.distance, .3);
}
