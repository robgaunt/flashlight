import java.util.ArrayDeque;

class PointTrail {
  final ArrayDeque<Point2D> points;
  final int maxPoints;

  public PointTrail(int maxPoints) {
    this.maxPoints = maxPoints;
    points = new ArrayDeque<Point2D>();
  }

  public void add(Point2D newPoint) {
    points.addLast(newPoint);
  }

  public void draw() {
    while (points.size() > maxPoints) {
      Point2D point = points.removeFirst();
    }
    int position = 0;
    for (Point2D point : points) {
      position++;
      stroke(255.0 * (float)position / points.size());
      ellipse(point.x, point.y, 5, 5); 
    }
  }
  
  public void clear() {
    points.clear();
  }
}

