import FloodFill from "q-floodfill";

self.onmessage = (
  event: MessageEvent<{
    data: Uint8ClampedArray<ArrayBuffer>;
    width: number;
    height: number;
    x: number;
    y: number;
    color: string;
  }>,
) => {
  try {
    const { data, width, height, x, y, color } = event.data;
    const fill = new FloodFill(new ImageData(data, width, height));
    fill.fill(color, x, y, 0);
    self.postMessage(
      { data: fill.imageData.data, changed: fill.modifiedPixelsCount > 0 },
      { transfer: [fill.imageData.data.buffer] },
    );
  } catch (error) {
    self.postMessage({
      error: error instanceof Error ? error.message : "Fill failed",
    });
  }
};
