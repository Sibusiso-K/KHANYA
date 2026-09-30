export function pixelForClick(clientX, clientY, rect, width, height) {
  return {
    x: Math.min(width - 1, Math.max(0, Math.floor((clientX - rect.left) / rect.width * width))),
    y: Math.min(height - 1, Math.max(0, Math.floor((clientY - rect.top) / rect.height * height))),
  };
}

export function fittedImageRect(rect, imageWidth, imageHeight, fit = 'contain') {
  if (fit !== 'contain') return rect;
  const scale = Math.min(rect.width / imageWidth, rect.height / imageHeight);
  const width = imageWidth * scale, height = imageHeight * scale;
  return {left: rect.left + (rect.width - width) / 2, top: rect.top + (rect.height - height) / 2, width, height};
}

export function grainIdAt(rgba, pixelIndex) {
  const offset = pixelIndex * 4;
  return rgba[offset] + 256 * rgba[offset + 1] + 65536 * rgba[offset + 2];
}

export function grainLiberationState(payloadFraction) {
  if (payloadFraction === 0) return 'NO VALUABLE MINERALS';
  return payloadFraction >= 0.5 ? 'FREE' : 'LOCKED';
}

export function formatPayloadPercent(payloadFraction) {
  const percent = payloadFraction * 100;
  return percent === 0 ? '0.0' : percent < 0.1 ? Number(percent.toPrecision(2)).toString() : percent.toFixed(1);
}

export function liberationExplanation(payloadFraction) {
  const state = grainLiberationState(payloadFraction);
  if (state === 'NO VALUABLE MINERALS') return 'No valuable mineral is present in this grain; liberation status does not apply.';
  if (state === 'LOCKED') return 'Valuable mineral is present, but below the 50% free-particle threshold.';
  return 'At least 50% valuable mineral; meets the advisor’s free-particle rule.';
}
