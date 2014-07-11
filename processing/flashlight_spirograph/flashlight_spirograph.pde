// general tweak parameter which adjusts the various inputs automatically over time

import java.util.Vector;
import controlP5.*;

//AndroidSetup androidSetup;
final int NUM_SEARCHLIGHTS = 4;
final SpirographPointProvider[] pointProviders = new SpirographPointProvider[NUM_SEARCHLIGHTS];
final SearchlightDirector[] searchlightDirectors = new SearchlightDirector[NUM_SEARCHLIGHTS];

final int MIN_ITERATION_TIME_MILLIS = 110;
final String oscNetAddress = "224.0.0.1";

Point2D centerPoint;
final int SLIDER_MARGIN = 100;
int SLIDER_WIDTH;
final int SLIDER_HEIGHT = 40;
final int RADIUS_ONE_MAX = 200;
final int RADIUS_ONE_MIN = 0;
final int RADIUS_ONE_INITIAL = 175;
final int RADIUS_TWO_MAX = 200;
final int RADIUS_TWO_MIN = 0;
final int RADIUS_TWO_INITIAL = 35;
final int POINT_DISTANCE_MAX = 200;
final int POINT_DISTANCE_MIN = 0;
final int POINT_DISTANCE_INITIAL = 150;
final float VELOCITY_MIN = 0.01;
final float VELOCITY_MAX = 0.15;
final float VELOCITY_INITIAL = 0.03;
final float CHASE_DISTANCE_MIN = 0;
final float CHASE_DISTANCE_MAX = 4 * PI;
final float CHASE_DISTANCE_INITIAL = PI / NUM_SEARCHLIGHTS;
int radiusOne = RADIUS_ONE_INITIAL;
int radiusTwo = RADIUS_TWO_INITIAL;
int pointDistance = POINT_DISTANCE_INITIAL;
float velocity = VELOCITY_INITIAL;
float chaseDistance = CHASE_DISTANCE_INITIAL;

// Initialize all to true so that we run initialization code on first loop.
boolean shapeChanged = true;
boolean velocityChanged = true;
boolean chaseDistanceChanged = true;

ControlP5 cp5;

void setup() {
//  size(800, 1280);
  // For running on a Macbook with Retina display:
  size(800, 1280, "processing.core.PGraphicsRetina2D");
  hint(ENABLE_RETINA_PIXELS);

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
  cp5.addSlider("chaseDistance")
      .setPosition(SLIDER_MARGIN, width + 8 * SLIDER_HEIGHT)
      .setSize(SLIDER_WIDTH, SLIDER_HEIGHT)
      .setRange(CHASE_DISTANCE_MIN, CHASE_DISTANCE_MAX)
      .setValue(CHASE_DISTANCE_INITIAL);

  for (int i = 0; i < NUM_SEARCHLIGHTS; ++i) {
    SpirographPointProvider pointProvider = new SpirographPointProvider(width, width);
    pointProvider.setRads(i * PI / NUM_SEARCHLIGHTS);
    SearchlightDirector searchlightDirector = new SearchlightDirector(
        new FlashlightOscClient(String.valueOf(i + 1), oscNetAddress, width, width),
        pointProvider);
    pointProviders[i] = pointProvider;
    searchlightDirectors[i] = searchlightDirector;
  }
}

void draw() {
  long start = millis();
  if (shapeChanged || velocityChanged) {
    for (SpirographPointProvider pointProvider : pointProviders) {
      pointProvider.init(centerPoint, radiusOne, radiusTwo, pointDistance, velocity);
    }
  }
  if (shapeChanged) {
    pointProviders[0].setRadsToBestMatch();
  }
  if (shapeChanged || chaseDistanceChanged) {
    for (int i = 1; i < NUM_SEARCHLIGHTS; ++i) {
      pointProviders[i].setRads(pointProviders[0].rads() + i * chaseDistance);
    }
  }

  shapeChanged = false;
  velocityChanged = false;
  chaseDistanceChanged = false;

  background(0);
  for (SearchlightDirector director : searchlightDirectors) {
    director.draw();
  }

  while (millis() - start < MIN_ITERATION_TIME_MILLIS) ;
}

void controlEvent(ControlEvent event) {
  shapeChanged = shapeChanged || event.isFrom("radiusOne")
      || event.isFrom("radiusTwo")
      || event.isFrom("pointDistance");
  velocityChanged = velocityChanged || event.isFrom("velocity");
  chaseDistanceChanged = chaseDistanceChanged || event.isFrom("chaseDistance");
}

