import {AuthImage,workspaceStorageKey} from './client';
import {useEffect, useMemo, useRef, useState} from 'react';
import * as THREE from 'three';
import {OrbitControls} from 'three/examples/jsm/controls/OrbitControls.js';
import {RotateCcw, Upload, Download, Layers, MapPin, ArrowRight, Box, Map, Scissors, Info, FileJson, Compass} from 'lucide-react';
import {parseSurvey, saveFile, surveyTemplate, type Survey} from './spatialData';

type Sample = {id: string; thumbnail_url: string};
type Props = {samples: Sample[]; selected: string; onSelect: (id: string) => void; onInspect: () => void; busy?: boolean};
type View = '3D' | 'Plan' | 'Section';
type Point = {id: string; x: number; y: number; z: number; depth: number; sampleId: string};
const rockColors = ['#a1b4a1', '#c0b699', '#748d9b', '#b7a2bc', '#536b7e'];
const rockNames = ['Weathered cover', 'Upper host', 'Marker horizon', 'Lower host', 'Basement'];
const relief = (x: number, z: number) => .19 * Math.sin(x * .8) + .16 * Math.cos(z * .9) + .10 * Math.sin(x + z * .4);
const horizon = (x: number, z: number, layer: number) => 2.3 - layer * .66 + relief(x, z) + x * .04;
const demos: Point[] = Array.from({length: 7}, (_, i) => {
  const x = [-3.5,-1.6,.3,2.4,3.6,-2,1.5][i], z = [-1.6,.7,-1.1,1.4,-.8,2.6,-2.5][i];
  return {id: `DEMO-${String(i + 1).padStart(2, '0')}`, x, y: -.55 + i % 3 * .27, z, depth: 3, sampleId: ''};
});

function RockScene({points, demo, selected, onPick, view, terrain, strata, collars, slice, exaggeration, resetKey}: {
  points: Point[]; demo: boolean; selected: string; onPick: (id: string) => void; view: View; terrain: boolean; strata: boolean; collars: boolean; slice: number; exaggeration: number; resetKey: number;
}) {
  const host = useRef<HTMLDivElement>(null);
  const cameraMemory = useRef<{key:string; position:THREE.Vector3; up:THREE.Vector3; target:THREE.Vector3; zoom:number}|null>(null);
  const pickRef = useRef(onPick); pickRef.current = onPick;
  const [error, setError] = useState('');
  useEffect(() => {
    if (!host.current) return;
    const el = host.current;
    let renderer: THREE.WebGLRenderer;
    try {renderer = new THREE.WebGLRenderer({antialias: true});} catch {setError('3D is unavailable on this device. The point list and survey export remain available.'); return;}
    setError('');
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2)); renderer.localClippingEnabled = true;
    renderer.setClearColor('#edf1f2'); el.appendChild(renderer.domElement);
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(-8, 8, 6, -6, .1, 120);
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true; controls.enableRotate = view === '3D'; controls.minZoom = .45; controls.maxZoom = 5;
    const targetY = demo ? .5 * exaggeration : Math.max(0,...points.map(p=>(p.y+p.depth)*exaggeration))/2;
    if (view === 'Plan') {camera.position.set(0, 25, .001); camera.up.set(0, 0, -1);} else if (view === 'Section') {camera.position.set(0, targetY, 25);} else {camera.position.set(13, 11, 16);}
    controls.target.set(0, targetY, 0);
    const cameraKey = `${demo}:${view}:${resetKey}:${exaggeration}`;
    const previous = cameraMemory.current;
    if(previous?.key===cameraKey){camera.position.copy(previous.position);camera.up.copy(previous.up);camera.zoom=previous.zoom;controls.target.copy(previous.target);}
    controls.update();
    scene.add(new THREE.HemisphereLight(0xffffff, 0x718090, 2.4));
    const sunlight = new THREE.DirectionalLight(0xffffff, 2.5); sunlight.position.set(-8, 14, 9); scene.add(sunlight);
    const model = new THREE.Group(); model.scale.y = exaggeration; scene.add(model);
    const grid = new THREE.GridHelper(14, 14, 0x99aab2, 0xd4dde1); grid.position.y = demo ? -1.12 : -.15; scene.add(grid);
    const clip = new THREE.Plane(new THREE.Vector3(0, 0, -1), slice + .002);
    const material = (color: string) => new THREE.MeshStandardMaterial({color, roughness: .92, side: THREE.DoubleSide, clippingPlanes: [clip]});
    if (demo) {
      // Authored procedural geometry for a labelled demonstration, never a model inference.
      for (let layer = 0; layer < 5; layer++) {
        if (layer === 0 ? !terrain : !strata) continue;
        const surface = new THREE.PlaneGeometry(10, 8, 70, 56); surface.rotateX(-Math.PI / 2);
        const attr = surface.getAttribute('position');
        for (let i = 0; i < attr.count; i++) attr.setY(i, horizon(attr.getX(i), attr.getZ(i), layer));
        surface.computeVertexNormals(); model.add(new THREE.Mesh(surface, material(rockColors[layer])));
        const positions: number[] = [];
        const edge = (x1: number, z1: number, x2: number, z2: number) => {
          for (let j = 0; j < 64; j++) {
            const a = j / 64, b = (j + 1) / 64;
            const x = x1 + (x2 - x1) * a, z = z1 + (z2 - z1) * a, xx = x1 + (x2 - x1) * b, zz = z1 + (z2 - z1) * b;
            const y = horizon(x,z,layer), yy = horizon(xx,zz,layer), low = layer === 4 ? -1 : horizon(x,z,layer+1), low2 = layer === 4 ? -1 : horizon(xx,zz,layer+1);
            positions.push(x,y,z, x,low,z, xx,yy,zz, xx,yy,zz, x,low,z, xx,low2,zz);
          }
        };
        edge(-5,-4,5,-4); edge(-5,-4,-5,4); edge(5,-4,5,4); edge(-5,4,5,4);
        // A real cap at the section slider, rather than an unclosed clipped shell.
        if (slice < 3.99) edge(-5,slice,5,slice);
        const wall = new THREE.BufferGeometry(); wall.setAttribute('position', new THREE.Float32BufferAttribute(positions,3)); wall.computeVertexNormals();
        model.add(new THREE.Mesh(wall, material(rockColors[layer])));
      }
    }
    const pickables: THREE.Mesh[] = [];
    if (collars) points.forEach(p => {
      const top = demo ? horizon(p.x,p.z,0) + .12 : p.y + p.depth;
      const bottom = demo ? p.y : p.y;
      const color = selected === p.id ? '#e57534' : '#285c88';
      const line = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(p.x,top,p.z), new THREE.Vector3(p.x,bottom,p.z)]);
      model.add(new THREE.Line(line, new THREE.LineBasicMaterial({color, depthTest: false, transparent: true, opacity: .8})));
      const marker = new THREE.Mesh(new THREE.SphereGeometry(selected === p.id ? .15 : .10,16,12), new THREE.MeshBasicMaterial({color, depthTest: false}));
      marker.position.set(p.x,bottom,p.z); marker.renderOrder = 3; marker.userData.id = p.id; model.add(marker); pickables.push(marker);
      const collar = new THREE.Mesh(new THREE.SphereGeometry(.075,12,8), new THREE.MeshBasicMaterial({color: '#ffffff', depthTest: false}));
      collar.position.set(p.x,top,p.z); collar.userData.id = p.id; model.add(collar); pickables.push(collar);
    });
    const ray = new THREE.Raycaster(); let down: [number,number] = [0,0];
    const pointerDown = (e: PointerEvent) => {down = [e.clientX,e.clientY];};
    const pointerUp = (e: PointerEvent) => {
      if (Math.hypot(e.clientX-down[0],e.clientY-down[1]) > 6) return;
      const r = el.getBoundingClientRect(); ray.setFromCamera(new THREE.Vector2((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1),camera);
      const hit = ray.intersectObjects(pickables)[0]; if(hit) pickRef.current(hit.object.userData.id);
    };
    renderer.domElement.addEventListener('pointerdown',pointerDown); renderer.domElement.addEventListener('pointerup',pointerUp);
    const resize = () => {const w=el.clientWidth,h=el.clientHeight; if(!w||!h)return; renderer.setSize(w,h); camera.left=-6.5*w/h;camera.right=6.5*w/h;camera.top=Math.max(6.5,targetY+1);camera.bottom=-camera.top;camera.left=-camera.top*w/h;camera.right=camera.top*w/h;camera.updateProjectionMatrix();};
    const ro = new ResizeObserver(resize); ro.observe(el); resize(); let frame=0;
    const draw = () => {frame=requestAnimationFrame(draw);controls.update();renderer.render(scene,camera);}; draw();
    return () => {cameraMemory.current={key:cameraKey,position:camera.position.clone(),up:camera.up.clone(),target:controls.target.clone(),zoom:camera.zoom};cancelAnimationFrame(frame);ro.disconnect();controls.dispose();renderer.domElement.removeEventListener('pointerdown',pointerDown);renderer.domElement.removeEventListener('pointerup',pointerUp);scene.traverse(o=>{const m=o as THREE.Mesh;m.geometry?.dispose();if(m.material)(Array.isArray(m.material)?m.material:[m.material]).forEach(v=>v.dispose());});renderer.dispose();renderer.domElement.remove();};
  }, [points,demo,selected,view,terrain,strata,collars,slice,exaggeration,resetKey]);
  return <><div className="geo-canvas" ref={host} role="img" aria-label={`${view} view of ${demo?'illustrative geology':'imported survey points'}. Use the point list for keyboard selection.`}/>{error&&<p className="geo-error" role="alert">{error}</p>}</>;
}

export default function Spatial({samples,selected,onSelect,onInspect,busy}: Props) {
  const [survey,setSurvey]=useState<Survey|null>(()=>{try{const raw=localStorage.getItem(workspaceStorageKey('survey-v1'));if(raw){const v=JSON.parse(raw);return parseSurvey(JSON.stringify(v.original),v.name);}}catch{}return null;});
  const [source,setSource]=useState<'demo'|'survey'>('survey');
  const [view,setView]=useState<View>('3D'),[terrain,setTerrain]=useState(true),[strata,setStrata]=useState(true),[collars,setCollars]=useState(true),[slice,setSlice]=useState(4),[exaggeration,setExaggeration]=useState(1),[resetKey,setResetKey]=useState(0),[pointId,setPointId]=useState('DEMO-01'),[error,setError]=useState('');
  const upload=useRef<HTMLInputElement>(null); const demo=source==='demo';
  const points=useMemo<Point[]>(()=>demo?demos:(survey?.points||[]).map(p=>({...p,x:p.x/survey!.span*10,y:p.y/survey!.span*10,z:p.z/survey!.span*10,depth:p.depth/survey!.span*10})),[demo,survey]);
  const current=points.find(p=>p.id===pointId)||points[0];
  const original=survey?.points.find(p=>p.id===current?.id);
  const linked=!demo&&current?.sampleId?samples.find(s=>s.id===current.sampleId):undefined;
  const currentSample=samples.find(s=>s.id===selected);
  function pick(id:string){setPointId(id);const p=points.find(p=>p.id===id);if(!demo&&p?.sampleId&&samples.some(s=>s.id===p.sampleId)&&!busy)onSelect(p.sampleId);}
  async function importSurvey(file?:File){if(!file)return;try{if(file.size>2_000_000)throw Error('Use a GeoJSON file smaller than 2 MB.');const parsed=parseSurvey(await file.text(),file.name);localStorage.setItem(workspaceStorageKey('survey-v1'),JSON.stringify({original:parsed.original,name:parsed.name}));setSurvey(parsed);setSource('survey');setPointId(parsed.points[0].id);setError('');setExaggeration(1);setSlice(4);}catch(e){setError(e instanceof Error?e.message:'Survey import failed.');}finally{if(upload.current)upload.current.value='';}}
  const linkedCount=survey?.points.filter(p=>samples.some(s=>s.id===p.sampleId)).length||0;
  return <div className="geo-workspace">
    <div className="geo-sourcebar"><label className="synthetic-toggle"><input aria-label="Show synthetic demo scene (not real data)" type="checkbox" checked={demo} onChange={e=>{setSource(e.target.checked?'demo':'survey');setPointId(e.target.checked?'DEMO-01':survey?.points[0]?.id||'');}}/><span>Show synthetic demo scene (not real data)</span></label><div className="geo-source-actions"><button className="button" onClick={()=>upload.current?.click()}><Upload size={15}/><span>{survey?'Import GeoJSON':'Import survey GeoJSON'}</span></button><button className="button" disabled={!survey} onClick={()=>saveFile(survey!.original,'reefprint-survey.geojson')}><Download size={15}/>Export survey</button><input ref={upload} hidden type="file" accept=".geojson,.json" onChange={e=>importSurvey(e.target.files?.[0])}/></div></div>
    {!demo&&!survey&&<section className="panel geo-empty-state"><h2>No survey imported</h2><p>Import a GeoJSON FeatureCollection of WGS84 Point features to view measured collar locations. Use coordinates [longitude, latitude, elevation in metres] and a numeric depth_m property; optional sample_id values link points to micrographs. No geological body is inferred from absent survey data.</p><button className="button primary" onClick={()=>upload.current?.click()}><Upload size={15}/>Import survey GeoJSON</button></section>}
    {error&&<p className="error-banner" role="alert">{error}</p>}
    <div className="geo-layout">
      <aside className="geo-sidebar"><div className="section-head"><div><h2><Layers size={16}/> Scene layers</h2><p>{demo?'Illustrative local coordinates':survey?.name}</p></div></div><div className="geo-layer-controls">{[[terrain,setTerrain,'Terrain surface'],[strata,setStrata,'Geological domains'],[collars,setCollars,'Collars & sample points']].map(([value,set,label],i)=><label key={String(label)}><input type="checkbox" checked={i<2&&!demo?false:Boolean(value)} disabled={i<2&&!demo} onChange={e=>(set as (v:boolean)=>void)(e.target.checked)}/><span>{String(label)}</span>{i<2&&<small>{demo?'Demo':'No data'}</small>}</label>)}</div>
      {demo&&<div className="geo-domain-legend"><h3>Illustrative lithology</h3>{rockNames.map((n,i)=><span key={n}><i style={{background:rockColors[i]}}/>{n}</span>)}<small>These colours describe rock units, not predicted mineral phases.</small></div>}
      <div className="geo-points"><h3>{demo?'Demo drillholes':'Survey records'} <small>{points.length}</small></h3>{points.map(p=><button aria-pressed={current?.id===p.id} className={current?.id===p.id?'selected':''} key={p.id} onClick={()=>pick(p.id)}><MapPin size={14}/><span>{p.id}<small>{demo?'Synthetic geometry':p.sampleId||'No sample link'}</small></span>{current?.id===p.id&&<span className="geo-selected-dot"/>}</button>)}</div></aside>
      <section className="geo-stage"><div className="geo-toolbar"><div className="segmented" aria-label="Spatial view">{([{name:'3D',icon:Box},{name:'Plan',icon:Map},{name:'Section',icon:Scissors}] as const).map(({name,icon:Icon})=><button key={name} className={view===name?'selected':''} aria-pressed={view===name} onClick={()=>setView(name)}><Icon size={14}/>{name==='Plan'?'Plan map':name==='Section'?'E–W section':'3D model'}</button>)}</div><button className="icon-button" aria-label="Reset spatial camera" onClick={()=>setResetKey(k=>k+1)}><RotateCcw size={17}/></button></div>
      <div className="geo-render"><RockScene points={points} demo={demo} selected={current?.id||''} onPick={pick} view={view} terrain={terrain} strata={strata} collars={collars} slice={slice} exaggeration={exaggeration} resetKey={resetKey}/><div className="geo-mode-label"><span className={'badge '+(demo?'amber':'neutral')}>{demo?'SYNTHETIC · NOT DATA':'Imported coordinates · user supplied'}</span></div><div className="geo-compass"><Compass size={26}/><span>{view==='Section'?'E–W / elevation':'North = −Z'}</span></div><div className="geo-scale">{demo?'Synthetic local units':survey?`Grid interval ≈ ${(survey.span/10).toFixed(0)} m`:'No coordinate grid'}<span>Vertical ×{exaggeration}</span></div></div>
      <div className="geo-bottom-controls"><label>Section cut<input aria-label="Section cut" type="range" min="-3.5" max="4" step=".1" value={slice} disabled={!demo} onChange={e=>setSlice(Number(e.target.value))}/><span>{slice===4?'Full block':slice.toFixed(1)}</span></label><label>Vertical scale<select aria-label="Vertical exaggeration" value={exaggeration} onChange={e=>setExaggeration(Number(e.target.value))}><option value="1">1×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label></div><p className="geo-instructions">{view==='3D'?'Drag to orbit.':'Drag to pan.'} Scroll to zoom. Select a point or use the record list. {view==='Section'?'All points projected east–west; this is not a thin section slice.':''}</p></section>
      <aside className="geo-inspector"><div className="section-head"><div><h2>{current?.id||'Select a point'}</h2><p>{demo?'Demonstration drillhole':'Survey point details'}</p></div><MapPin size={19}/></div><dl className="geo-properties">{demo?<><dt>Coordinates</dt><dd>Synthetic</dd><dt>Interpretation</dt><dd>Procedural layers</dd><dt>Sample linkage</dt><dd>None</dd></>:<><dt>Longitude</dt><dd>{original?.lon.toFixed(6)}°</dd><dt>Latitude</dt><dd>{original?.lat.toFixed(6)}°</dd><dt>Collar elevation</dt><dd>{original?.elevation} m</dd><dt>Depth</dt><dd>{original?.depth} m</dd><dt>Sample ID</dt><dd>{original?.sampleId||'Not provided'}</dd></>}</dl>
      <div className="geo-inspector-note"><Info size={16}/><p>{demo?'Explore the viewing workflow here. These layers and drillholes are synthetic and are not linked to S2 images.':'Collar-to-sample traces are vertical approximations. No downhole survey, terrain interpolation or orebody estimation is applied.'}</p></div>
      <div className="geo-sample-preview"><h3>{linked?'Linked micrograph':'Current analysis sample'}</h3>{(linked||currentSample)&&<AuthImage src={(linked||currentSample)!.thumbnail_url} alt={'Micrograph '+(linked||currentSample)!.id}/>}<strong>{linked?.id||selected}</strong><p>{linked?'This sample ID matches the imported record.':demo?'Shown separately for analysis; not located in this demo.':'No matching image at this point. The current analysis sample is shown separately.'}</p><button className="button primary" disabled={busy} onClick={()=>{if(linked)onSelect(linked.id);onInspect();}}>Open mineral analysis <ArrowRight size={15}/></button></div></aside>
    </div>
    <div className="geo-evidence-bridge"><div><h3>Location supplies context. The image supplies phase evidence.</h3><p>A spatial selection opens its linked micrograph. The model produces a phase map; the report records measured test performance; a separate simulator demonstrates a reviewed parameter change.</p></div><button className="button" disabled={busy} onClick={onInspect}>Continue with {selected}<ArrowRight size={15}/></button></div>
    <details className="geo-import-help"><summary><FileJson size={16}/>Connect QGIS or your field survey</summary><div><p>In QGIS, export Point features as GeoJSON in WGS84 (EPSG:4326), with Z values containing collar elevation in metres. Include <code>id</code>, <code>sample_id</code> and numeric <code>depth_m</code>. Exact sample IDs connect records to the library. Only import coordinates you have validated.</p><p>Up to 500 points, 2 MB and a 25 km radius. The display uses a local equirectangular approximation; exports retain the original coordinates. No online basemap or paid API is required. Imports stay in this browser.</p><button className="button" onClick={()=>saveFile(surveyTemplate,'reefprint-format-example.geojson')}><Download size={15}/>Download format example</button>{survey&&<button className="text-button" onClick={()=>{localStorage.removeItem(workspaceStorageKey('survey-v1'));setSurvey(null);setSource('demo');setPointId('DEMO-01');}}>Clear imported survey</button>}<span>{survey?`${linkedCount} / ${survey.points.length} imported records match sample IDs.`:'No survey imported yet.'}</span></div></details>
  </div>;
}
