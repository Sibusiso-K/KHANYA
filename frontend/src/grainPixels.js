export function decodeGrainId(rgba, pixelIndex = 0) {
  const offset = pixelIndex * 4;
  return rgba[offset] + 256 * rgba[offset + 1] + 65536 * rgba[offset + 2];
}
