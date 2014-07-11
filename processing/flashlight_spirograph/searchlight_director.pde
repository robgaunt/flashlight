class SearchlightDirector {
  private final FlashlightOscClient oscClient;
  private final PointProvider pointProvider;
  private final PointTrail pointTrail;

  public SearchlightDirector(
      FlashlightOscClient oscClient, PointProvider pointProvider) {
    this.oscClient = oscClient;
    this.pointProvider = pointProvider;
    pointTrail = new PointTrail(20);
  }

  public void draw() {
    Point2D next = pointProvider.nextPoint();
    pointTrail.add(next);
    pointTrail.draw();
    oscClient.drawGrid(next);
  }
}
  
