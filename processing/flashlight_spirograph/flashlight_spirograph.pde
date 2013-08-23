import controlP5.*;

//AndroidSetup androidSetup;
SpirographPointProvider sc;
PointTrail pointTrail;
FlashlightOscClient oscClient;

final int MIN_ITERATION_TIME_MILLIS = 100;
final String oscNetAddress = "224.0.0.1";

Point2D centerPoint;
final int SLIDER_MARGIN = 100;
int SLIDER_WIDTH;
final int SLIDER_HEIGHT = 40;
final int RADIUS_ONE_MAX = 200;
final int RADIUS_ONE_MIN = 0;
final int RADIUS_ONE_INITIAL = 50;
final int RADIUS_TWO_MAX = 200;
final int RADIUS_TWO_MIN = 0;
final int RADIUS_TWO_INITIAL = 100;
final int POINT_DISTANCE_MAX = 200;
final int POINT_DISTANCE_MIN = 0;
final int POINT_DISTANCE_INITIAL = 50;
final float VELOCITY_MIN = 0.01;
final float VELOCITY_MAX = 0.1;
final float VELOCITY_INITIAL = 0.03;
int radiusOne = RADIUS_ONE_INITIAL;
int radiusTwo = RADIUS_TWO_INITIAL;
int pointDistance = POINT_DISTANCE_INITIAL;
float velocity = VELOCITY_INITIAL;
int lastRadiusOne = 0;
int lastRadiusTwo = 0;
int lastPointDistance = 0;
float lastVelocity = 0;

ControlP5 cp5;

void setup() {
  size(800,1280);
  background(0);
  smooth();
  
  centerPoint = new Point2D(width / 2.0, width / 2.0);
  SLIDER_WIDTH = width - 2 * SLIDER_MARGIN;

//  androidSetup = new AndroidSetup();
//  androidSetup.acquireLocks();

  cp5 = new ControlP5(this);
  cp5.addSlider("radiusOne")
      .setPosition(SLIDER_MARGIN, width)
      .setSize(SLIDER_WIDTH, SLIDER_HEIGHT)
      .setRange(RADIUS_ONE_MIN, RADIUS_ONE_MAX)
      .setValue(RADIUS_ONE_INITIAL);
  cp5.addSlider("radiusTwo")
      .setPosition(SLIDER_MARGIN, width + 2 * SLIDER_HEIGHT)
      .setSize(SLIDER_WIDTH, SLIDER_HEIGHT)
      .setRange(RADIUS_TWO_MIN, RADIUS_TWO_MAX)
      .setValue(RADIUS_TWO_INITIAL);
  cp5.addSlider("pointDistance")
      .setPosition(SLIDER_MARGIN, width + 4 * SLIDER_HEIGHT)
      .setSize(SLIDER_WIDTH, SLIDER_HEIGHT)
      .setRange(POINT_DISTANCE_MIN, POINT_DISTANCE_MAX)
      .setValue(POINT_DISTANCE_INITIAL);
  cp5.addSlider("velocity")
      .setPosition(SLIDER_MARGIN, width + 6 * SLIDER_HEIGHT)
      .setSize(SLIDER_WIDTH, SLIDER_HEIGHT)
      .setRange(VELOCITY_MIN, VELOCITY_MAX)
      .setValue(VELOCITY_INITIAL);

  oscClient = new FlashlightOscClient("1", oscNetAddress, width, width);
  pointTrail = new PointTrail(100);
  sc = new SpirographPointProvider(width, width);
}

void draw() {
  if (lastRadiusOne != radiusOne
      || lastRadiusTwo != radiusTwo
      || lastPointDistance != pointDistance
      || lastVelocity != velocity) {
    lastRadiusOne = radiusOne;
    lastRadiusTwo = radiusTwo;
    lastPointDistance = pointDistance;
    lastVelocity = velocity;
    sc.init(centerPoint, radiusOne, radiusTwo, pointDistance, velocity);
  }
  Point2D next = sc.nextPoint();
  pointTrail.add(next);
  pointTrail.draw();
  oscClient.drawGrid(next);
}

