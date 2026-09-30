import {useEffect,useRef,useState} from 'react';
import {MessageSquare,Send,ArrowRight,Loader2,FileText,ShieldCheck,AlertCircle} from 'lucide-react';
import {api} from './client';
import './assistant.css';

export type AssistantProposal={id:string;action:'openReports'|'openSpatial'|'runAnalysis'|'addNote';label:string;args:Record<string,string>};
type Evidence={label:string;kind:'predicted'|'measured'|'simulated';value:string};
type Answer={answer:string;mode:'local-evidence'|'provider';evidence:Evidence[];proposals:AssistantProposal[];warnings:string[]};
type ProviderStatus={local_available:boolean;provider_ready:boolean;provider:string|null;model:string|null;context_policy:string};
type Exchange={question:string;response:Answer;sampleId:string;resultId?:string|null};
const prompts=['Summarise this result','How accurate is the model?','Explain the process advisory','What does the spatial view require?'];
const allowedActions=new Set(['openReports','openSpatial','runAnalysis','addNote']);

export default function AssistantPanel({sampleId,resultId,onExecute,busy=false}:{sampleId:string;resultId?:string|null;onExecute:(proposal:AssistantProposal)=>Promise<void>|void;busy?:boolean}){
 const [question,setQuestion]=useState(''),[exchanges,setExchanges]=useState<Exchange[]>([]),[status,setStatus]=useState<ProviderStatus|null>(null),[pending,setPending]=useState(false),[external,setExternal]=useState(false),[consent,setConsent]=useState(false),[error,setError]=useState(''),[executing,setExecuting]=useState<string|null>(null),[applied,setApplied]=useState<Record<string,string>>({});
 const current=useRef({sampleId,resultId});current.current={sampleId,resultId};const requestCounter=useRef(0),reply=useRef<HTMLDivElement>(null);
 useEffect(()=>{let cancelled=false;api<ProviderStatus>('/assistant/status').then(value=>{if(!cancelled)setStatus(value)}).catch(()=>{if(!cancelled)setStatus(null)});return()=>{cancelled=true}},[]);
 useEffect(()=>{requestCounter.current+=1;setExchanges([]);setQuestion('');setError('');setPending(false);setApplied({});setConsent(false)},[sampleId]);
 useEffect(()=>{if(exchanges.length)reply.current?.scrollIntoView({block:'nearest',behavior:'auto'})},[exchanges.length]);
 async function ask(text=question){
  if(!text.trim()||pending||text.length>3000)return;const serial=++requestCounter.current,sample=sampleId,id=resultId;setPending(true);setError('');
  try{const response=await api<Answer>('/assistant',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:text.trim(),sample_id:sample,result_id:id||null,use_provider:external,context_opt_in:consent})});if(serial!==requestCounter.current||current.current.sampleId!==sample||current.current.resultId!==id)return;setExchanges(items=>[...items.slice(-5),{question:text.trim(),response,sampleId:sample,resultId:id}]);setQuestion('')}
  catch(reason:any){if(serial===requestCounter.current)setError(reason.message||'The evidence helper could not respond. Try again.')}
  finally{if(serial===requestCounter.current)setPending(false)}
 }
 async function execute(proposal:AssistantProposal,key:string,exchange:Exchange){
  if(!allowedActions.has(proposal.action)||executing||busy)return;
  if(exchange.sampleId!==sampleId||exchange.resultId!==resultId){setError('This proposal belongs to an earlier result. Ask again against the current sample.');return}
  if(proposal.action==='addNote'&&(!proposal.args.note||proposal.args.note.length>3000)){setError('That note proposal is invalid. Add a shorter note manually.');return}
  setExecuting(key);setError('');try{await onExecute(proposal);setApplied(items=>({...items,[key]:proposal.action==='addNote'?'Added to editable draft; save the sample record to keep it.':proposal.action==='runAnalysis'?'Analysis requested. Follow the scan workspace for its result.':'Workspace opened.'}))}catch(reason:any){setError(reason.message||'The task could not run. Nothing was saved automatically.')}finally{setExecuting(null)}
 }
 return <section className="assistant-panel" aria-label="Mineral evidence assistant">
  <div className="assistant-intro"><MessageSquare size={22}/><div><h2>Ask the evidence</h2><p>Interpret this specimen, find its report, prepare the next task.</p></div></div>
  <div className="assistant-scope"><ShieldCheck size={16}/><span>{external?'Provider explanations':'Local evidence helper'}<small>Selected sample: {sampleId.replaceAll('_',' ')}. {resultId?'A completed result is in scope.':'No completed result yet.'}</small></span></div>
  <div className="assistant-prompts" aria-label="Suggested evidence questions">{prompts.map(prompt=><button type="button" key={prompt} disabled={pending||(external&&!consent)} onClick={()=>void ask(prompt)}>{prompt}<ArrowRight size={13}/></button>)}</div>
  <details className="assistant-provider"><summary>Language model connection</summary><p>{status?.provider_ready?`Server configured for ${status.provider} / ${status.model}.`:'No language model is configured. The local helper still works without a key or subscription.'}</p><label><input type="checkbox" checked={external} disabled={!status?.provider_ready||pending} onChange={event=>{setExternal(event.target.checked);setConsent(false)}}/>Use the configured language model</label>{external&&<label className="assistant-consent"><input type="checkbox" checked={consent} disabled={pending} onChange={event=>setConsent(event.target.checked)}/><span>Share this question and selected result/report facts with {status?.provider}. Images, audio, saved notes and coordinates are excluded. The question itself is shared; do not include secrets.</span></label>}<small>A language model explains evidence; the segmentation model identifies pixels. Provider output is generated text, not a measured result. No task or plant control runs automatically.</small></details>
  <div className="assistant-conversation" aria-live="polite" aria-relevant="additions">
   {!exchanges.length&&<div className="assistant-empty"><FileText size={24}/><h3>Keep the answer tied to its source</h3><p>Ask about phases, scope, confidence, accuracy or the simulator. Each answer carries its evidence type. To draft an observation, write “Add note: …”.</p></div>}
   {exchanges.map((exchange,index)=><article className="assistant-exchange" key={index}>
    <p className="assistant-question">{exchange.question}</p><div className="assistant-answer">{exchange.response.answer}</div><span className="assistant-mode">{exchange.response.mode==='provider'?'Generated explanation':'From local evidence'}</span>
    <ul className="assistant-sources" aria-label="Answer evidence">{exchange.response.evidence.map((item,i)=><li key={i}><span className={'assistant-kind '+item.kind}>{item.kind}</span><div>{item.label}<small title={item.value}>{item.value}</small></div></li>)}</ul>
    {exchange.response.proposals.map(proposal=>{const key=index+'-'+proposal.id,stale=exchange.resultId!==resultId;return <div key={key} className="assistant-task">{proposal.action==='addNote'&&<blockquote>{proposal.args.note}</blockquote>}<button type="button" className="button" disabled={!!executing||busy||!!applied[key]||stale||!allowedActions.has(proposal.action)} onClick={()=>void execute(proposal,key,exchange)}>{executing===key?<Loader2 size={15} className="spin"/>:<ArrowRight size={15}/>} {proposal.label}</button>{applied[key]&&<p role="status">{applied[key]}</p>}{stale&&<small>This proposal belongs to an earlier result; ask again.</small>}</div>})}
    {exchange.response.warnings.map((warning,i)=><p className="assistant-warning" key={i}>{warning}</p>)}
   </article>)}<div ref={reply}/>
  </div>
  {pending&&<p className="assistant-working" role="status"><Loader2 className="spin" size={16}/>{external?'Requesting a provider explanation…':'Reading the selected evidence…'}</p>}
  {error&&<p className="assistant-error" role="alert"><AlertCircle size={16}/>{error}</p>}
  <form className="assistant-composer" onSubmit={event=>{event.preventDefault();void ask()}}><label htmlFor="reefprint-evidence-question">Your question<textarea id="reefprint-evidence-question" rows={3} maxLength={3000} value={question} onChange={event=>setQuestion(event.target.value)} placeholder="What did this image show, and how reliable is it?"/></label><button type="submit" className="button primary" disabled={pending||!question.trim()||(external&&!consent)}><Send size={15}/>Ask about this sample</button></form>
 </section>
}
