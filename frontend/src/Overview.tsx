import {ArrowRight, Database, FileCheck2, Microscope, Server} from 'lucide-react';
import {AuthImage} from './client';

type Props = {
  samples: {id:string;thumbnail_url:string;dimensions:number[];dataset:string;has_prediction:boolean}[];
  selected:string;
  result:{id:string;result_id:string|null;scope?:string;confidence:number|null;model_sha:string;prediction_source:string}|null;
  report:{checkpoint_matches_report:boolean;report_source:string;model_sha:string;metrics:{mean_iou:number;n_test_images:number}|null}|null;
  health:{checkpoint_available?:boolean;cloud_sync?:boolean;deployment?:string}|null;
  loading:boolean;busy:boolean;
  onNavigate:(page:string)=>void;
  onSelect:(id:string)=>void;
};
const title=(s:string)=>s.replaceAll('_',' ').replace(/\b\w/g,c=>c.toUpperCase());
export default function Overview({samples,selected,result,report,health,loading,busy,onNavigate,onSelect}:Props){
 const analysed=samples.filter(s=>s.has_prediction), active=samples.find(s=>s.id===selected);
 if(result?.id!==selected)result=null;
 return <div className="overview-grid">
  <section className="panel overview-library"><div className="section-head"><div><h2>Research library</h2><p>Specimens returned by the connected service</p></div><Database size={20}/></div>
   <div className="overview-counts"><div><strong>{loading?'—':samples.length}</strong><span>Micrographs</span></div><div><strong>{loading?'—':analysed.length}</strong><span>With current saved analysis</span></div></div>
   <div className="overview-specimens">{samples.slice(0,6).map(s=><button key={s.id} disabled={busy} onClick={()=>{onSelect(s.id);onNavigate('Workspace')}}><AuthImage src={s.thumbnail_url} alt=""/><span><strong>{title(s.id)}</strong><small>{s.has_prediction?'Analysis available':'Ready to analyse'}</small></span><ArrowRight size={16}/></button>)}</div>
   {!samples.length&&!loading&&<p className="empty-inline">Add a reflected-light micrograph to start your library.</p>}
   <button className="text-button overview-link" onClick={()=>onNavigate('Samples')}>Open sample library <ArrowRight size={15}/></button>
  </section>
  <section className="panel overview-active"><div className="section-head"><div><h2>Continue your inspection</h2><p>Selected specimen and its current evidence</p></div><Microscope size={20}/></div>
   {active?<><AuthImage className="overview-micrograph" src={active.thumbnail_url} alt={'Reflected-light micrograph '+selected}/><div className="overview-content"><h3>{title(selected)}</h3><p>{active.dataset} · {active.dimensions.join(' × ')} px</p><dl><dt>Prediction</dt><dd>{result?.result_id?result.prediction_source:'Awaiting analysis'}</dd><dt>Scope</dt><dd>{result?.result_id?result.scope||'Recorded inference':'Original acquisition'}</dd><dt>Confidence</dt><dd>{result?.result_id&&result.confidence!=null?(result.confidence*100).toFixed(1)+'% · uncalibrated':'Not available'}</dd></dl><button className="button primary" onClick={()=>onNavigate('Workspace')}>Inspect specimen <ArrowRight size={15}/></button></div></>:<p className="empty-inline">Choose a specimen in the library to inspect its image and phase evidence.</p>}
  </section>
  <aside className="overview-side"><section className="panel overview-evidence"><div className="section-head"><div><h2>Checkpoint evidence</h2><p>Recorded evaluation, with its source</p></div><FileCheck2 size={20}/></div><div className="overview-content">{report?.metrics?<><strong className="overview-score">{report.metrics.mean_iou.toFixed(3)}</strong><p>Mean IoU, including background<br/>{report.metrics.n_test_images} held-out sections</p></>:<p>No matching evaluation is available.</p>}<span className={'badge '+(report?.checkpoint_matches_report?'green':'amber')}>{report?.checkpoint_matches_report?'Checkpoint matches report':'Report match unavailable'}</span><p className="overview-source">{report?.report_source||'Evidence source unavailable'}</p><button className="text-button" onClick={()=>onNavigate('Reports')}>Read evidence and limitations <ArrowRight size={15}/></button></div></section>
   <section className="panel overview-service"><div className="section-head"><div><h2>Service status</h2><p>Connection and model readiness</p></div><Server size={20}/></div><div className="overview-content"><dl><dt>API</dt><dd>{health?'Connected':loading?'Connecting…':'Unavailable'}</dd><dt>Checkpoint</dt><dd>{health?.checkpoint_available?'Available':'Unavailable'}</dd><dt>Deployment</dt><dd>{health?.deployment||'Unknown'}</dd><dt>Cloud sync</dt><dd>{health?.cloud_sync?'Connected':'Not connected'}</dd></dl><p className="overview-source">Phase fractions describe the analysed image. They are not ore grade. Process actions run in the research simulator.</p></div></section>
  </aside>
 </div>
}
