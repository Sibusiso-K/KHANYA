export type SurveyPoint = { id: string; sampleId: string; lon: number; lat: number; elevation: number; depth: number; x: number; y: number; z: number };
export type Survey = { name: string; points: SurveyPoint[]; original: unknown; span: number; origin: [number, number, number] };

// Deliberately narrow interchange contract. Reject rather than silently reproject.
export function parseSurvey(text: string, name: string): Survey {
  const input = JSON.parse(text);
  if (input.type !== 'FeatureCollection' || !Array.isArray(input.features) || !input.features.length || input.features.length > 500) throw Error('Use a GeoJSON FeatureCollection with 1–500 Point features.');
  if (input.crs) throw Error('Export RFC 7946 GeoJSON in WGS84 longitude/latitude without a legacy CRS member.');
  const seen = new Set<string>();
  const points: SurveyPoint[] = input.features.map((f: any, i: number) => {
    const c = f.geometry?.coordinates, p = f.properties || {};
    if (f.type !== 'Feature' || f.geometry?.type !== 'Point' || !Array.isArray(c) || c.length !== 3 || !c.every((v: unknown) => typeof v === 'number' && Number.isFinite(v))) throw Error(`Feature ${i + 1}: Point coordinates must be [longitude, latitude, collar elevation in metres].`);
    if (Math.abs(c[0]) > 180 || Math.abs(c[1]) > 85 || Math.abs(c[2]) > 12000) throw Error(`Feature ${i + 1}: coordinates are outside supported geographic bounds.`);
    const id = p.id ?? f.id ?? `point-${i + 1}`;
    if ((typeof id !== 'string' && typeof id !== 'number') || !String(id).trim() || seen.has(String(id))) throw Error('Every point needs a unique ID.');
    seen.add(String(id));
    if (typeof p.depth_m !== 'number' || !Number.isFinite(p.depth_m) || p.depth_m < 0 || p.depth_m > 12000) throw Error(`Feature ${i + 1}: depth_m must be a number from 0 to 12000.`);
    if (p.sample_id != null && typeof p.sample_id !== 'string') throw Error(`Feature ${i + 1}: sample_id must be text.`);
    return {id: String(id), sampleId: p.sample_id || '', lon: c[0], lat: c[1], elevation: c[2], depth: p.depth_m, x: 0, y: 0, z: 0};
  });
  const lon = points.reduce((s, p) => s + p.lon, 0) / points.length;
  const lat = points.reduce((s, p) => s + p.lat, 0) / points.length;
  const elevation = Math.min(...points.map(p => p.elevation - p.depth));
  points.forEach(p => { p.x = (p.lon - lon) * 111320 * Math.cos(lat * Math.PI / 180); p.z = -(p.lat - lat) * 111320; p.y = p.elevation - p.depth - elevation; });
  const extent = Math.max(...points.map(p => Math.abs(p.x)), ...points.map(p => Math.abs(p.z)));
  if (extent > 25000) throw Error('This local viewer supports sites within 25 km of the centre. Split the survey in QGIS.');
  const span = Math.max(100, extent * 2, ...points.map(p => p.y + p.depth));
  return {name, points, original: input, span, origin: [lon, lat, elevation]};
}

export function saveFile(data: unknown, filename: string) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type: 'application/geo+json'}));
  const a = document.createElement('a'); a.href = url; a.download = filename; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const surveyTemplate = {
  type: 'FeatureCollection',
  features: [{type: 'Feature', properties: {id: 'EXAMPLE-ONLY', sample_id: 'replace-with-your-sample-id', depth_m: 0, note: 'Synthetic format example. Replace every coordinate with your survey.'}, geometry: {type: 'Point', coordinates: [28, -26, 1500]}}]
};
