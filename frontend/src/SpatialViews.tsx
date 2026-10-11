import {useId, useMemo, useRef, useState} from 'react';
import {Crosshair, Minus, Plus, Maximize2, MapPin} from 'lucide-react';
import {fitMap, gridInterval, inSection, localToWgs84, zoomMap, type MapExtent, type MapPoint} from './spatialGeometry';
import type {Survey} from './spatialData';

// Leave enough left gutter for a complete elevation such as 1,500 at mobile scale.
const W = 800, H = 510, L = 120, T = 30, PW = 655, PH = 416;
const fmt = (value: number) => value.toLocaleString(undefined, {maximumFractionDigits: 1});
const scaleLabel = (metres: number) => metres >= 1000 ? `${fmt(metres / 1000)} km` : `${fmt(metres)} m`;
type Props = {points: MapPoint[]; selected: string; onPick: (id: string) => void; survey: Survey | null; demo: boolean; collars: boolean};

export function PlanSurvey({points, selected, onPick, survey, demo, collars}: Props) {
  const initial = useMemo(() => fitMap(points, PW / PH, demo ? 1 : 30), [points, demo]);
  const [extent, setExtent] = useState<MapExtent>(initial);
  const [cursor, setCursor] = useState<{x: number; z: number} | null>(null);
  const svg = useRef<SVGSVGElement>(null);
  const drag = useRef<{px: number; py: number; extent: MapExtent; moved: boolean} | null>(null);
  const clipId = useId().replace(/:/g, '');
  const toX = (x: number) => L + ((x - extent.cx) / extent.width + .5) * PW;
  const toZ = (z: number) => T + ((z - extent.cz) / extent.height + .5) * PH;
  const query = (clientX: number, clientY: number) => {
    const rect = svg.current!.getBoundingClientRect();
    const x = (clientX - rect.left) / rect.width * W, y = (clientY - rect.top) / rect.height * H;
    return {px: x, py: y, x: extent.cx + ((x - L) / PW - .5) * extent.width, z: extent.cz + ((y - T) / PH - .5) * extent.height};
  };
  const step = gridInterval(extent.width);
  const xTicks = Array.from({length: 20}, (_, i) => Math.ceil((extent.cx - extent.width / 2) / step) * step + i * step).filter(v => v <= extent.cx + extent.width / 2);
  const zTicks = Array.from({length: 20}, (_, i) => Math.ceil((extent.cz - extent.height / 2) / step) * step + i * step).filter(v => v <= extent.cz + extent.height / 2);
  const scale = gridInterval(extent.width * .95);
  const geo = cursor && !demo && survey ? localToWgs84(cursor.x, cursor.z, survey.origin) : null;
  const current = points.find(p => p.id === selected);
  return <div className="survey-map">
    <div className="survey-map-tools"><div><MapPin size={15}/><span>{demo ? 'Synthetic plan grid' : 'Survey map'}<small>{demo ? 'Illustrative local units' : 'WGS84 collars · local metric grid'}</small></span></div><div>
      <button className="icon-button" aria-label="Zoom map in" onClick={() => setExtent(e => zoomMap(e, .75))}><Plus size={17}/></button>
      <button className="icon-button" aria-label="Zoom map out" onClick={() => setExtent(e => zoomMap(e, 1.33))}><Minus size={17}/></button>
      <button className="icon-button" aria-label="Fit all survey points" onClick={() => setExtent(initial)}><Maximize2 size={16}/></button>
      <button className="icon-button" aria-label="Centre map on selected point" disabled={!current} onClick={() => current && setExtent(e => ({...e, cx: current.x, cz: current.z}))}><Crosshair size={17}/></button>
    </div></div>
    <svg ref={svg} viewBox={`0 0 ${W} ${H}`} className="survey-map-svg" role="img" aria-label="Interactive plan map. Drag to pan; select a point or use the survey record list."
      onPointerDown={e => {if ((e.target as Element).closest('[data-map-point]')) return; const q = query(e.clientX, e.clientY); drag.current = {px: q.px, py: q.py, extent, moved: false}; e.currentTarget.setPointerCapture(e.pointerId);}}
      onPointerMove={e => {const q = query(e.clientX, e.clientY); setCursor(q); if (drag.current) {const d = drag.current; if (Math.hypot(q.px - d.px, q.py - d.py) > 3) d.moved = true; setExtent({...d.extent, cx: d.extent.cx - (q.px - d.px) / PW * d.extent.width, cz: d.extent.cz - (q.py - d.py) / PH * d.extent.height});}}}
      onPointerUp={e => {drag.current = null; if(e.currentTarget.hasPointerCapture(e.pointerId))e.currentTarget.releasePointerCapture(e.pointerId);}}
      onPointerCancel={() => {drag.current = null;}} onPointerLeave={() => {if (!drag.current)setCursor(null);}}>
      <defs><clipPath id={clipId}><rect x={L} y={T} width={PW} height={PH}/></clipPath></defs>
      <rect x={L} y={T} width={PW} height={PH} fill="#f8fafb" stroke="#ccd9df"/>
      <g clipPath={`url(#${clipId})`}>
        {xTicks.map(x => <line key={`x${x}`} x1={toX(x)} x2={toX(x)} y1={T} y2={T + PH} stroke={x === 0 ? '#abbfc8' : '#e0e8ed'}/>)}
        {zTicks.map(z => <line key={`z${z}`} x1={L} x2={L + PW} y1={toZ(z)} y2={toZ(z)} stroke={z === 0 ? '#abbfc8' : '#e0e8ed'}/>)}
        {collars && points.map(p => <g key={p.id} data-map-point={p.id} className="survey-map-point" onClick={() => onPick(p.id)}><title>{p.id}{p.sampleId ? ` · ${p.sampleId}` : ''}</title>{selected === p.id && <circle cx={toX(p.x)} cy={toZ(p.z)} r={16} fill="#e5753420" stroke="#e5753470"/>}<circle cx={toX(p.x)} cy={toZ(p.z)} r={selected === p.id ? 7 : 5} fill={selected === p.id ? '#e57534' : '#285c88'} stroke="white" strokeWidth="2"/><text x={toX(p.x) + 11} y={toZ(p.z) - 10} fill="#2c4559" fontSize="12">{p.id}</text></g>)}
      </g>
      {xTicks.filter((_,i)=>i%2===0).map(x => <text key={`tx${x}`} x={toX(x)} y={T + PH + 22} textAnchor="middle" className="survey-axis-value">{fmt(x)}</text>)}
      {zTicks.filter((_,i)=>i%2===0).map(z => <text key={`tz${z}`} x={L - 10} y={toZ(z) + 4} textAnchor="end" className="survey-axis-value">{fmt(-z)}</text>)}
      <text x={L + PW / 2} y={H - 10} textAnchor="middle" className="survey-axis-title">East from site centre ({demo ? 'local units' : 'm'})</text>
      <text transform={`translate(17 ${T + PH / 2}) rotate(-90)`} textAnchor="middle" className="survey-axis-title">North from site centre ({demo ? 'local units' : 'm'})</text>
      <g transform={`translate(${L + PW + 12} ${T + 35})`}><path d="M0 -22 L-5 -4 L0 -8 L5 -4 Z" fill="#38556a"/><text y="12" textAnchor="middle" fontSize="12" fill="#38556a">N</text></g>
      <g transform={`translate(${L + 18} ${T + PH - 26})`}><rect x="-8" y="-18" width={Math.min(PW*.25, scale / extent.width * PW)+28} height="42" fill="#ffffffde"/><path d={`M0 -5 V0 H${scale / extent.width * PW} V-5`} fill="none" stroke="#41576a" strokeWidth="2"/><text y="16" fontSize="11" fill="#41576a">{demo ? `${fmt(scale)} local units` : scaleLabel(scale)}</text></g>
    </svg>
    <div className="survey-map-status"><span>{geo ? `${Math.abs(geo[1]).toFixed(6)}° ${geo[1]<0?'S':'N'} / ${Math.abs(geo[0]).toFixed(6)}° ${geo[0]<0?'W':'E'}` : cursor ? `E ${fmt(cursor.x)} / N ${fmt(-cursor.z)} ${demo ? 'units' : 'm'}` : 'Move over the grid to query coordinates'}</span><span>{collars ? points.length : 0} points visible</span></div>
    {!demo && <p className="survey-map-disclosure">An offline survey grid. Terrain imagery and geology are not supplied by this GeoJSON.</p>}
  </div>;
}

export function SurveySection({survey, selected, onPick, collars, exaggeration, centre, width}: {survey: Survey; selected: string; onPick: (id: string) => void; collars: boolean; exaggeration: number; centre: number; width: number}) {
  const visible = inSection(survey.points, centre, width);
  const bounds = fitMap(survey.points, PW / PH);
  const low = Math.min(...survey.points.map(p => p.elevation - p.depth)), high = Math.max(...survey.points.map(p => p.elevation));
  const ySpan = Math.max(30, high - low);
  // The same metre scale on both axes; exaggeration is explicit and labels remain real elevations.
  const metresPerPixel = Math.max(bounds.width / PW, ySpan * exaggeration / (PH * .82));
  const horizontalSpan = metresPerPixel * PW;
  const yMid = (low + high) / 2;
  const x = (east: number) => L + PW / 2 + (east-bounds.cx) / metresPerPixel;
  const y = (elevation: number) => T + PH / 2 - (elevation - yMid) / metresPerPixel * exaggeration;
  const xStep = gridInterval(horizontalSpan), yStep = gridInterval(metresPerPixel * PH / exaggeration);
  const xs = Array.from({length: 20}, (_,i)=>Math.ceil((bounds.cx-horizontalSpan/2)/xStep)*xStep+i*xStep).filter(v=>v<=bounds.cx+horizontalSpan/2);
  const yMin = yMid - metresPerPixel*PH/2/exaggeration, yMax = yMid + metresPerPixel*PH/2/exaggeration;
  const ys = Array.from({length:20},(_,i)=>Math.ceil(yMin/yStep)*yStep+i*yStep).filter(v=>v<=yMax);
  return <div className="survey-section"><div className="survey-section-header"><strong>East–west section</strong><span>{visible.length} / {survey.points.length} records in corridor</span></div><svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label="East–west survey section showing collar elevations and straight vertical depth traces. Select a record from the list for keyboard access.">
    <rect x={L} y={T} width={PW} height={PH} fill="#f8fafb" stroke="#ccd9df"/>
    {xs.map(v=><g key={`x${v}`}><line x1={x(v)} x2={x(v)} y1={T} y2={T+PH} stroke="#e0e8ed"/><text x={x(v)} y={T+PH+22} textAnchor="middle" className="survey-axis-value">{fmt(v)}</text></g>)}
    {ys.map(v=><g key={`y${v}`}><line x1={L} x2={L+PW} y1={y(v)} y2={y(v)} stroke="#e0e8ed"/><text x={L-9} y={y(v)+4} textAnchor="end" className="survey-axis-value">{fmt(v)}</text></g>)}
    {collars && visible.map(p=><g key={p.id} className="survey-map-point" onClick={()=>onPick(p.id)}><title>{p.id}: collar {p.elevation} m; depth {p.depth} m</title><line x1={x(p.x)} x2={x(p.x)} y1={y(p.elevation)} y2={y(p.elevation-p.depth)} stroke={selected===p.id?'#e57534':'#285c88'} strokeWidth={selected===p.id?4:2}/><circle cx={x(p.x)} cy={y(p.elevation)} r="5" fill="white" stroke={selected===p.id?'#e57534':'#285c88'} strokeWidth="2"/><circle cx={x(p.x)} cy={y(p.elevation-p.depth)} r="6" fill={selected===p.id?'#e57534':'#285c88'} stroke="white" strokeWidth="2"/><text x={x(p.x)+9} y={y(p.elevation)-9} fontSize="12" fill="#2c4559">{p.id}</text></g>)}
    {!visible.length && <text x={L+PW/2} y={T+PH/2} textAnchor="middle" fill="#586e80" fontSize="15">No records in this section corridor</text>}
    <text x={L+PW/2} y={H-10} textAnchor="middle" className="survey-axis-title">East from site centre (m)</text><text transform={`translate(17 ${T+PH/2}) rotate(-90)`} textAnchor="middle" className="survey-axis-title">Elevation (m)</text>
  </svg><div className="survey-map-status"><span>North centre {fmt(-centre)} m · corridor {fmt(width)} m wide</span><span>Vertical ×{exaggeration}</span></div><p className="survey-map-disclosure">Straight vertical traces from the supplied collar and depth. Downhole inclination is not available; no lithology is inferred.</p></div>;
}
