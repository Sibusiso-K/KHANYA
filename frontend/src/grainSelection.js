export function pixelForClick(clientX, clientY, rect, width, height) {
  return {
    x: Math.min(width - 1, Math.max(0, Math.floor((clientX - rect.left) / rect.width * width))),
    y: Math.min(height - 1, Math.max(0, Math.floor((clientY - rect.top) / rect.height * height))),
  };
}

export function grainIdAt(rgba, pixelIndex) {
  const offset = pixelIndex * 4;
  return rgba[offset] + 256 * rgba[offset + 1] + 65536 * rgba[offset + 2];
}
