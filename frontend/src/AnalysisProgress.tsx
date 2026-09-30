import {useEffect,useState} from 'react';
import {ScanLine,CheckCircle2} from 'lucide-react';
type Progress={stage?:string;completed?:number;total?:number;box?:number[];image_size?:number[]};
const stages=['preparing','segmenting','measuring','saving'];
const names=['Preparing image and model','Identifying mineral phases','Measuring grain associations','Saving evidence'];
export default function AnalysisProgress({progress,status,startedAt,mode}:{progress?:Progress;status?:string;startedAt:number;mode:string}){
 const [seconds,setSeconds]=useState(0);
 useEffect(()=>{const tick=()=>setSeconds(Math.max(0,Math.floor((Date.now()-startedAt)/1000)));tick();const timer=setInterval(tick,1000);return()=>clearInterval(timer)},[startedAt]);
 const stage=progress?.stage||'queued',index=stages.indexOf(stage);
 return <div className="analysis-scan" aria-label="Analysis in progress"><div className="scan-reticle" aria-hidden="true"><span/><span/><span/><span/><div className="scan-beam"/></div><section className="scan-status"><div className="scan-heading"><ScanLine size={22}/><div><strong>{status==='queued'?'Waiting for the analysis worker':names[index]||'Starting analysis'}</strong><small>{seconds}s elapsed · {mode==='full'?'Full-section analysis':'Six-field analysis'}</small></div></div><ol>{stages.map((s,i)=><li key={s} className={i<index?'done':i===index?'current':''}>{i<index?<CheckCircle2 size={15}/>:<span className="stage-dot"/>}{names[i]}</li>)}</ol><p role="status" aria-live="polite">{stage==='segmenting'&&progress?.total?`${progress.completed||0} / ${progress.total} ${mode==='full'?'tiles':'fields'} classified`:stage==='queued'?'Your job is queued. The scan animation is a waiting indicator.':'Processing your image. Phase results appear after completion.'}</p>{stage==='segmenting'&&!!progress?.total&&<progress aria-label="Classified fields or tiles" max={progress.total} value={progress.completed||0}/>}<small>Live job status · animation is illustrative · no predictions shown before completion</small></section></div>;
}
