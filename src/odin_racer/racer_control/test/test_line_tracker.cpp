#include "racer_control/line_tracker.hpp"
#include <gtest/gtest.h>
#include <limits>
using namespace racer_control;
TEST(Tracker, StraightAndSignedCorrection) {
  auto straight = pursuit({{.2, 0}, {.6, 0}}, .4, .05, .5);
  ASSERT_TRUE(straight.valid);
  EXPECT_DOUBLE_EQ(straight.v, .05);
  EXPECT_DOUBLE_EQ(straight.w, 0);
  auto left = pursuit({{.2, .04}, {.6, .04}}, .4, .05, .5);
  auto right = pursuit({{.2, -.04}, {.6, -.04}}, .4, .05, .5);
  EXPECT_GT(left.w, 0);
  EXPECT_NEAR(left.w, -right.w, 1e-12);
}

TEST(Tracker, CircleCurvatureAndYawBound) {
  std::vector<Point> path;
  for (int i = 0; i <= 100; i++) {
    double a = i * .01;
    path.push_back({.8 * std::sin(a), .8 * (1 - std::cos(a))});
  }
  auto command = pursuit(path, .4, .05, .5);
  ASSERT_TRUE(command.valid);
  EXPECT_NEAR(command.w / command.v, 1 / .8, .001);
  auto limited = pursuit(path, .4, .2, .1);
  ASSERT_TRUE(limited.valid);
  EXPECT_LE(std::abs(limited.w), .1 + 1e-12);
  EXPECT_LT(limited.v, .2);
}

TEST(Tracker, InvalidAndInsufficientPaths) {
  EXPECT_FALSE(pursuit({}, .4, .05, .5).valid);
  EXPECT_FALSE(pursuit({{.2, 0}, {.3, 0}}, .4, .05, .5).valid);
  EXPECT_FALSE(pursuit({{-.6, 0}, {-.2, 0}}, .4, .05, .5).valid);
  EXPECT_FALSE(
      pursuit({{.2, 0}, {.6, std::numeric_limits<double>::quiet_NaN()}}, .4, .05, .5).valid);
}

TEST(Tracker, FreshnessAndAcceleration) {
  EXPECT_TRUE(fresh(10, 9.9, .35));
  EXPECT_FALSE(fresh(10, 9, .35));
  EXPECT_FALSE(fresh(10, 11, .35));
  EXPECT_FALSE(fresh(10, 0, .35));
  EXPECT_FALSE(fresh(10, std::numeric_limits<double>::quiet_NaN(), .35));
  EXPECT_NEAR(slew(0, .05, .15, .02), .003, 1e-12);
  EXPECT_NEAR(slew(.05, 0, .15, .02), .047, 1e-12);
}

TEST(Tracker, ArcOrderAllowsLateralExitButRejectsJumps) {
  EXPECT_TRUE(ordered_path({{.25, 0}, {.30, 0}, {.35, 0}, {.35, .05}, {.35, .1}}));
  EXPECT_FALSE(ordered_path({{.25, 0}, {.6, 0}, {.6, .1}}));
  EXPECT_FALSE(ordered_path({{.25, 0}, {.25, 0}, {.3, 0}}));
}

TEST(Tracker, AdaptiveBoundsAndTargetJumpGuard) {
  std::vector<Point> path;
  for (int i = 0; i < 100; ++i)
    path.push_back({.25 + i * .005, .02});
  auto c = adaptive_pursuit(path, .4, .28, .45, .05, .03, .5, .15);
  ASSERT_TRUE(c.valid);
  EXPECT_GE(c.lookahead, .28);
  EXPECT_LE(c.lookahead, .45);
  Point old{.70, .02};
  EXPECT_FALSE(adaptive_pursuit(path, .4, .28, .45, .05, .03, .5, .15, &old).valid);
  path.resize(5);
  EXPECT_FALSE(adaptive_pursuit(path, .4, .28, .45, .05, .03, .5, .15).valid);
}

TEST(Corner, StableEvidenceStopTurnAndDistinctReacquisitionFrames) {
  CornerTurn turn;
  std::string error;
  turn.observe(1, {.5, 0}, M_PI / 2, 0, {0, 0}, 0);
  EXPECT_FALSE(turn.update(1, {0, 0}, 0, 0, 0, false, 1, error).valid);
  turn.observe(1.1, {.501, 0}, M_PI / 2, 0, {.1, 0}, 0);
  turn.observe(1.2, {.5, 0}, M_PI / 2, 0, {.2, 0}, 0);
  EXPECT_TRUE(turn.update(1.2, {.2, 0}, 0, 0, 0, false, 1.2, error).valid);
  EXPECT_EQ(turn.phase, CornerTurn::Phase::APPROACH);
  auto stop = turn.update(8, {.485, 0}, 0, .01, 0, false, 8, error);
  EXPECT_DOUBLE_EQ(stop.v, 0);
  EXPECT_EQ(turn.phase, CornerTurn::Phase::STOP);
  turn.update(8.4, {.485, 0}, 0, 0, 0, false, 8.4, error);
  EXPECT_EQ(turn.phase, CornerTurn::Phase::TURN);
  auto rotate = turn.update(8.5, {.485, 0}, .1, 0, 0, false, 8.5, error);
  EXPECT_GT(rotate.w, 0);
  EXPECT_DOUBLE_EQ(rotate.v, 0);
  turn.update(13, {.485, 0}, M_PI / 2, 0, 0, false, 13, error);
  EXPECT_EQ(turn.phase, CornerTurn::Phase::REACQUIRE);
  for (int i = 0; i < 10; ++i)
    turn.update(13.1, {.485, 0}, M_PI / 2, 0, 0, true, 13.1, error);
  EXPECT_EQ(turn.phase, CornerTurn::Phase::REACQUIRE);
  turn.update(13.2, {.485, 0}, M_PI / 2, 0, 0, true, 13.2, error);
  turn.update(13.3, {.485, 0}, M_PI / 2, 0, 0, true, 13.3, error);
  EXPECT_EQ(turn.phase, CornerTurn::Phase::TRACK);
  EXPECT_TRUE(turn.consumed);
  EXPECT_TRUE(error.empty());
}

TEST(Corner, MemoryAndMissingExitFailClosedBothDirections) {
  for (int sign : {-1, 1}) {
    CornerTurn turn;
    std::string error;
    for (int i = 0; i < 3; ++i)
      turn.observe(1 + i * .1, {.3, 0}, sign * M_PI / 2, 0, {0, 0}, 0);
    turn.update(1.2, {0, 0}, 0, 0, 0, false, 1.2, error);
    EXPECT_FALSE(turn.update(20, {.1, 0}, 0, 0, 0, false, 20, error).valid);
    EXPECT_EQ(error, "corner_memory_limit");
  }
}

TEST(Corner, DistanceAngleAndExitTimeoutAreIndependentStops) {
  auto setup = []() {
    CornerTurn t;
    for (int i = 0; i < 3; ++i)
      t.observe(1 + i * .1, {.3, 0}, M_PI / 2, 0, {0, 0}, 0);
    std::string e;
    t.update(1.2, {0, 0}, 0, 0, 0, false, 1.2, e);
    return t;
  };
  {
    auto t = setup();
    std::string e;
    t.update(2, {.46, 0}, 0, 0, 0, false, 2, e);
    EXPECT_EQ(e, "corner_memory_limit");
  }
  {
    auto t = setup();
    std::string e;
    t.update(2, {0, 0}, 2., 0, 0, false, 2, e);
    EXPECT_EQ(e, "corner_memory_limit");
  }
  {
    auto t = setup();
    std::string e;
    t.update(2, {.285, 0}, 0, 0, 0, false, 2, e);
    t.update(2.4, {.285, 0}, 0, 0, 0, false, 2.4, e);
    t.update(7, {.285, 0}, M_PI / 2, 0, 0, false, 7, e);
    EXPECT_EQ(t.phase, CornerTurn::Phase::REACQUIRE);
    auto command = t.update(9.6, {.285, 0}, M_PI / 2, 0, 0, false, 9.6, e);
    EXPECT_FALSE(command.valid);
    EXPECT_EQ(e, "exit_not_reacquired");
  }
}

TEST(Tracker, SharedSegmentEndpointSurvivesFloatingPointMotionCompensation) {
  for (int k = 0; k < 1000; ++k) {
    std::vector<Point> path;
    double shift = .05 * std::abs(std::sin(k * 13.37)), yaw = 1e-6 * std::sin(k * 1.33);
    for (int i = 0; i < 80; ++i) {
      double x = .31 + i * .005 - shift;
      path.push_back({x * std::cos(yaw), x * std::sin(yaw)});
    }
    double radius = std::hypot(path.front().x, path.front().y) + .025;
    auto command = pursuit(path, radius, .05, .5);
    ASSERT_TRUE(command.valid) << "Centered acquisition " << k;
    EXPECT_NEAR(std::hypot(command.target.x, command.target.y), radius, 1e-10);
  }
}

TEST(Tracker, ShortVisiblePathSlowsWhileKeepingObservedLookahead) {
  std::vector<Point> path;
  for (int i = 0; i <= 22; ++i)
    path.push_back({.27 + i * .005, -.03});
  auto command = adaptive_pursuit(path, .4, .28, .45, .05, .05, .5, .15);
  ASSERT_TRUE(command.valid);
  EXPECT_GT(command.v, .005);
  EXPECT_LT(command.v, .035);
  EXPECT_GT(command.target.x, path.front().x);
  EXPECT_LT(command.target.x, path.back().x);
}

TEST(Tracker, ObservedHistoryRetainsBlindPrefixButDoesNotJoinSeparateLines) {
  std::vector<Point> old{{.1, 0}, {.15, 0}, {.2, 0}, {.25, 0}, {.3, 0}};
  auto joined = merge_observed_path(old, {{.2, .002}, {.25, .002}, {.3, .002}, {.35, .002}});
  EXPECT_DOUBLE_EQ(joined.front().x, .1);
  EXPECT_DOUBLE_EQ(joined.back().x, .35);
  auto separate = merge_observed_path(old, {{.2, .2}, {.25, .2}, {.3, .2}});
  EXPECT_DOUBLE_EQ(separate.front().y, 0.);
  EXPECT_EQ(separate.size(), old.size());
}
