import oscP5.*;
import netP5.*;

// Helper class to send OSC messages to a searchlight.
class FlashlightOscClient {
  private final OscP5 oscToSearchlights;
  private final String searchlightName;
  private final int gridWidth, gridHeight;

  public FlashlightOscClient(
      String searchlightName, String netAddress, int gridWidth, int gridHeight) {
    oscToSearchlights = new OscP5(this, oscNetAddress, 8888);
    this.searchlightName = searchlightName;
    this.gridWidth = gridWidth;
    this.gridHeight = gridHeight;
  }

  public void drawGrid(Point2D point) {
    OscMessage message = new OscMessage("/" + searchlightName + "/draw_grid");
    message.add(point.x / gridWidth);
    message.add(point.y / gridHeight);
    oscToSearchlights.send(message);
  }
}

