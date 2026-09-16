#include "racer_perception/line_geometry.hpp"
#include <gtest/gtest.h>
using namespace racer_perception;
TEST(FishPoly, VendorConventionAndAxis) {
  FishPoly camera{{400, 3, 800, 0, 410, 648, 0, 0, 1}, {.01,-.02,.03,-.01,.001,-.002}};
  camera.validate();
  auto axis = camera.project({0, 0, 1});
  EXPECT_DOUBLE_EQ(axis.x, 800); EXPECT_DOUBLE_EQ(axis.y, 648);
  double theta = .6, radius = theta;
  for (size_t i=0; i<6; ++i) radius += camera.d[i]*std::pow(theta, i+2);
  auto projected = camera.project({std::sin(theta)/std::sqrt(2.), std::sin(theta)/std::sqrt(2.), std::cos(theta)});
  EXPECT_NEAR(projected.x, 800+403*radius/std::sqrt(2.), 1e-10);
  EXPECT_NEAR(projected.y, 648+410*radius/std::sqrt(2.), 1e-10);
  EXPECT_LT(camera.project({0,0,-1}).x, 0);
  camera.d.clear(); EXPECT_THROW(camera.validate(), std::invalid_argument);
}
class LineTest : public testing::Test {
 protected:
  Grid grid;
  cv::Mat gray{grid.rows(), grid.cols(), CV_8UC1, cv::Scalar(180)};
  cv::Mat visible{gray.size(), CV_8UC1, cv::Scalar(255)};
  void line(double offset, double curvature=0) {
    for (int row=0; row<gray.rows; ++row) {
      double x = grid.point(row,0).x;
      double y = offset+curvature*x*x/2;
      int col = std::lround((grid.half_width-y)/grid.step);
      if(col>=2 && col<gray.cols-2) gray.row(row).colRange(col-2,col+2).setTo(0);
    }
  }
  Detection run() { return detect(gray,visible,grid,65,.008,.05,.18,.12); }
};
TEST_F(LineTest, OffsetAndCurve) {
  line(.025,.3); auto result=run(); ASSERT_TRUE(result.valid());
  for(auto p:result.points) EXPECT_NEAR(p.y,.025+.15*p.x*p.x,.008);
}
TEST_F(LineTest, BlankAndInvisibleNeverMeanCentered) {
  EXPECT_FALSE(run().valid()); line(0); visible.setTo(0); EXPECT_FALSE(run().valid());
}
TEST_F(LineTest, ForkAndCrossingRejected) {
  line(-.03); line(.03); EXPECT_EQ(run().reason,"ambiguous_branches");
  gray.setTo(180); line(0); gray.rowRange(30,35).setTo(0);
  // A full-width run is clipped and breaks the observed path before the crossing.
  EXPECT_FALSE(run().valid());
  gray.setTo(180); line(0); gray.rowRange(30,35).colRange(45,75).setTo(0);
  EXPECT_EQ(run().reason,"ambiguous_branches");
}
TEST_F(LineTest, ShortAndEdgeClippedRejected) {
  line(0); gray.rowRange(10,gray.rows).setTo(180); EXPECT_FALSE(run().valid());
  gray.setTo(180); gray.colRange(0,4).setTo(0); EXPECT_FALSE(run().valid());
}

TEST_F(LineTest, DistantCrossingTruncatesWithoutSelectingBranch) {
  line(0); gray.rowRange(75,80).colRange(45,75).setTo(0);
  auto result=run(); ASSERT_TRUE(result.valid());
  EXPECT_EQ(result.end_reason,"ambiguous_branches");
  EXPECT_LT(result.points.back().x,grid.point(75,0).x);
}

TEST_F(LineTest, LeftAndRightCornersKeepLateralExit) {
  for(int sign: {-1,1}) {
    gray.setTo(180);
    int center=grid.cols()/2, row=50;
    cv::line(gray,{center,0},{center,row},{0},4);
    cv::line(gray,{center,row},{center-sign*50,row},{0},4);
    auto result=run();ASSERT_TRUE(result.valid()) << result.reason;
    ASSERT_TRUE(result.corner_valid);
    EXPECT_NEAR(result.corner.x,.50,.015);EXPECT_NEAR(result.corner.y,0,.015);
    EXPECT_GT(sign*result.exit_direction.y,.9);
    EXPECT_GT(sign*result.points.back().y,.20);
    EXPECT_NEAR(result.points.back().x,result.corner.x,.015);
  }
}
TEST_F(LineTest, ConnectedSCurveAndDisconnectedNoise) {
  std::vector<cv::Point> path;
  for(int r=0;r<grid.rows();++r)path.push_back({60+int(12*std::sin(r*.06)),r});
  cv::polylines(gray,path,false,{0},4);
  cv::circle(gray,{10,40},3,{0},-1);
  auto result=run();ASSERT_TRUE(result.valid());EXPECT_FALSE(result.corner_valid);
  EXPECT_GT(result.points.size(),80u);
  for(size_t i=1;i<result.points.size();++i)EXPECT_LT(cv::norm(result.points[i]-result.points[i-1]),.008);
}
TEST_F(LineTest, InvisibleGapIsNotBridgedAndPriorCannotPickRemoteLine) {
  line(0);visible.rowRange(20,24).setTo(0);EXPECT_FALSE(run().valid());
  visible.setTo(255);
  SeedHint hint{{.25,.25},{1,0},true};
  EXPECT_FALSE(detect(gray,visible,grid,65,.008,.05,.18,.12,hint).valid());
}

TEST_F(LineTest, BlindBoundaryFragmentsNeverInventMultipleExits) {
  cv::line(gray,{15,10},{55,8},{0},4);cv::line(gray,{65,8},{105,10},{0},4);
  auto result=run();EXPECT_FALSE(result.valid());EXPECT_LT(result.exits,2u);
  EXPECT_EQ(result.reason,"insufficient_visible_length");
}

TEST_F(LineTest, HintDirectionUsesSupportedChordNotPixelEdge) {
  line(0,.6);
  for(int row=2;row<18;++row) {
    auto point=grid.point(row,0);point.y=.3*point.x*point.x;
    SeedHint hint{point,{1,-.02},true};
    auto d=detect(gray,visible,grid,65,.008,.05,.18,.12,hint);
    EXPECT_TRUE(d.valid()) << row << " " << d.reason;
  }
}

TEST_F(LineTest, ShortVisibleCurveUsesConfiguredLengthAndConfidence) {
  line(0., -1.2);
  gray.rowRange(27, gray.rows).setTo(180);
  EXPECT_FALSE(run().valid());
  auto result=detect(gray,visible,grid,65,.008,.05,.10,.12);
  ASSERT_TRUE(result.valid()) << result.reason;
  EXPECT_GE(result.confidence,.5);
  EXPECT_FALSE(result.corner_valid);
}
