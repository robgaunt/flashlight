/**
 * A PointProvider which uses a spirograph algorithm.
 * The original point calculation code is from http://www.openprocessing.org/sketch/17230.
 */
class SpirographPointProvider implements PointProvider {
  private Point2D center = null;
  private float r1 = 0;
  private float r2 = 0;
  private float h = 0;
  private float velocity = 0;
  private float rads = 0;
  private final int maxWidth, maxHeight;
  private boolean parametersChanged;
  private Point2D lastPoint;
  private static final int maxIterationsOnParameterChange = 1000;
 
  public SpirographPointProvider(int maxWidth, int maxHeight) {
    this.maxWidth = maxWidth;
    this.maxHeight = maxHeight;
  }
 
  public void init(
      Point2D center, float radiusOne, float radiusTwo, float pointDistance, float velocity) {
    this.parametersChanged = radiusOne != r1 || radiusTwo != r2 || pointDistance != h;
    this.center = center;
    r1 = radiusOne;
    r2 = radiusTwo;
    h = pointDistance;
    this.velocity = velocity;
  }

  public Point2D nextPoint() {
    if (parametersChanged && lastPoint != null) {
      double minDistance = Double.MAX_VALUE;
      float bestRads = rads;
      for (int i = 0; i < maxIterationsOnParameterChange; ++i) {
        Point2D candidate = nextPoint(rads);
        double distance = candidate.distance(lastPoint);
        if (distance < minDistance) {
          minDistance = distance;
          bestRads = rads;
        }
        rads += velocity;
      }
      rads = bestRads;
      parametersChanged = false;
    } else {
      rads += velocity;
    }
    lastPoint = nextPoint(rads);
    return lastPoint;
  }
  
  private Point2D nextPoint(float rads) {
    float x = center.x + (r1 - r2) * cos(rads) + h * cos((r1-r2)/r2*rads);
    float y = center.y + (r1 - r2) * sin(rads) + h * sin((r1-r2)/r2*rads);
    // Clip point to bounds.
    x = x > maxWidth ? maxWidth : x;
    x = x < 0 ? 0 : x;
    y = y > maxHeight ? maxHeight : y;
    y = y < 0 ? 0 : y;
    return new Point2D(x, y);
  }
}

