import java.lang.Math;

/**
 * Represents an (x, y) point on a plane.
 */
public class Point2D {
  public final float x, y;
  public Point2D(float x, float y) {
    this.x = x;
    this.y = y;
  }
  public double distance(Point2D other) {
    float deltaX = other.x - x;
    float deltaY = other.y - y;
    return Math.sqrt(deltaX * deltaX + deltaY * deltaY);
  }
}

