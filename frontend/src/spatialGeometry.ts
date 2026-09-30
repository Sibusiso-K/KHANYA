export type MapPoint = {id: string; x: number; z: number; sampleId: string};
export type MapExtent = {cx: number; cz: number; width: number; height: number};

/** Fit local metres (or explicitly synthetic units) without distorting the axes. */
export function fitMap(points: MapPoint[], aspect = 1.65, minimumSpan = 30): MapExtent {
  if (!points.length) return {cx: 0, cz: 0, width: 100, height: 100 / aspect};
  const xs = points.map(p => p.x), zs = points.map(p => p.z);
  const left = Math.min(...xs), right = Math.max(...xs), top = Math.min(...zs), bottom = Math.max(...zs);
  let width = Math.max(right - left, minimumSpan) * 1.35, height = Math.max(bottom - top, minimumSpan) * 1.35;
  if (width / height < aspect) width = height * aspect; else height = width / aspect;
  return {cx: (left + right) / 2, cz: (top + bottom) / 2, width, height};
}

/** Geographic query uses the same local approximation as parseSurvey, not a second CRS. */
export function localToWgs84(x: number, z: number, origin: [number, number, number]): [number, number] {
  return [origin[0] + x / (111320 * Math.cos(origin[1] * Math.PI / 180)), origin[1] - z / 111320];
}

export function gridInterval(span: number): number {
  const raw = span / 6;
  const magnitude = Math.pow(10, Math.floor(Math.log10(Math.max(raw, 0.00001))));
  const base = raw / magnitude;
  return (base <= 1 ? 1 : base <= 2 ? 2 : base <= 5 ? 5 : 10) * magnitude;
}

/** The section corridor is north–south width around an east–west section. */
export function inSection<T extends {z: number}>(points: T[], centreZ: number, width: number): T[] {
  return points.filter(p => Math.abs(p.z - centreZ) <= width / 2 + 1e-9);
}

export function zoomMap(extent: MapExtent, factor: number): MapExtent {
  const width = Math.min(250000, Math.max(1, extent.width * factor));
  return {...extent, width, height: width * extent.height / extent.width};
}
