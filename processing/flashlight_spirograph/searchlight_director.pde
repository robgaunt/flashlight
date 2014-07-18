class SearchlightDirector {
  private final FlashlightOscClient oscClient;
  private final PointProvider pointProvider;
  private final PointTrail pointTrail;
  private boolean enabled;

  public SearchlightDirector(
      FlashlightOscClient oscClient, PointProvider pointProvider) {
    this.oscClient = oscClient;
    this.pointProvider = pointProvider;
    pointTrail = new PointTrail(20);
    enabled = true;
  }

  public void draw() {
    // Keep advancing the point even if this is not enabled.
    Point2D next = pointProvider.nextPoint();
    if (enabled) {
      pointTrail.add(next);
      pointTrail.draw();
      oscClient.drawGrid(next);
    }
  }
  
  public void setEnabled(boolean enabled) {
    this.enabled = enabled;
    pointTrail.clear();
  }
}
  
