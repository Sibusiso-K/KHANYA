import {useEffect,useRef,useState} from 'react';
import {Mic,Square,Download,FilePlus,AlertCircle} from 'lucide-react';
import './assistant.css';

type RecognitionEvent={resultIndex:number;results:ArrayLike<{isFinal:boolean;0:{transcript:string}}>};
type Recognition={lang:string;continuous:boolean;interimResults:boolean;onresult:((event:RecognitionEvent)=>void)|null;onerror:((event:{error:string})=>void)|null;onend:(()=>void)|null;start:()=>void;stop:()=>void;abort:()=>void};
type SpeechWindow=Window&{SpeechRecognition?:new()=>Recognition;webkitSpeechRecognition?:new()=>Recognition};

export default function VoiceNotes({onAppend,disabled=false}:{onAppend:(text:string)=>void;disabled?:boolean}){
 const [draft,setDraft]=useState(''),[interim,setInterim]=useState(''),[consent,setConsent]=useState(false),[speechAvailable,setSpeechAvailable]=useState(false),[recordAvailable,setRecordAvailable]=useState(false),[active,setActive]=useState<'speech'|'audio'|null>(null),[requesting,setRequesting]=useState(false),[error,setError]=useState(''),[status,setStatus]=useState(''),[audio,setAudio]=useState<{url:string;extension:string}|null>(null);
 const recognition=useRef<Recognition|null>(null),recorder=useRef<MediaRecorder|null>(null),stream=useRef<MediaStream|null>(null),recordTimer=useRef<ReturnType<typeof setTimeout>|null>(null),mounted=useRef(true),baseDraft=useRef(''),finalText=useRef('');
 useEffect(()=>{mounted.current=true;const win=window as SpeechWindow;setSpeechAvailable(!!(win.SpeechRecognition||win.webkitSpeechRecognition));setRecordAvailable(window.isSecureContext&&!!navigator.mediaDevices?.getUserMedia&&typeof MediaRecorder!=='undefined');return()=>{mounted.current=false;recognition.current?.abort();if(recorder.current?.state==='recording')recorder.current.stop();stream.current?.getTracks().forEach(track=>track.stop());if(recordTimer.current)clearTimeout(recordTimer.current)}},[]);
 useEffect(()=>()=>{if(audio)URL.revokeObjectURL(audio.url)},[audio]);
 function stop(){recognition.current?.stop();if(recorder.current?.state==='recording')recorder.current.stop();stream.current?.getTracks().forEach(track=>track.stop());if(recordTimer.current)clearTimeout(recordTimer.current)}
 function dictate(){
  if(disabled||active||requesting||!consent)return;
  const win=window as SpeechWindow,Constructor=win.SpeechRecognition||win.webkitSpeechRecognition;
  if(!Constructor){setError('This browser does not support speech-to-text. Type your note or record audio locally.');return}
  const speech=new Constructor();recognition.current=speech;baseDraft.current=draft.trim();finalText.current='';setError('');setStatus('Waiting for microphone permission…');setInterim('');
  speech.lang='en-ZA';speech.continuous=true;speech.interimResults=true;
  speech.onresult=event=>{let pending='';for(let i=event.resultIndex;i<event.results.length;i++){const part=event.results[i];if(part.isFinal)finalText.current+=' '+part[0].transcript;else pending+=' '+part[0].transcript}if(mounted.current){setDraft((baseDraft.current+' '+finalText.current).trim().slice(0,8000));setInterim(pending.trim());setStatus('Listening. Review the transcript before adding it to your notes.')}};
  speech.onerror=event=>{if(mounted.current){setError(event.error==='not-allowed'?'Microphone or browser speech permission was denied. Allow it in browser settings, or type a note.':event.error==='network'?'Browser speech service could not connect. Type your note or record audio locally.':'Speech-to-text stopped ('+event.error+'). Your existing draft is kept.');setActive(null);setRequesting(false);setInterim('')}};
  speech.onend=()=>{if(mounted.current){setActive(null);setRequesting(false);setInterim('');setStatus('Microphone stopped. Check mineral names and numbers in the draft.')}};
  try{speech.start();setActive('speech');setStatus('Microphone active. Speak your observation.')}catch{setError('Speech-to-text could not start. Use typed notes or try a supported browser.');setActive(null)}
 }
 async function recordAudio(){
  if(disabled||active||requesting||!recordAvailable)return;
  setError('');setStatus('Waiting for microphone permission…');setRequesting(true);
  try{
   const input=await navigator.mediaDevices.getUserMedia({audio:true});if(!mounted.current){input.getTracks().forEach(track=>track.stop());return}stream.current=input;
   const mime=['audio/webm;codecs=opus','audio/ogg;codecs=opus','audio/mp4'].find(type=>MediaRecorder.isTypeSupported(type));
   const capture=new MediaRecorder(input,mime?{mimeType:mime,audioBitsPerSecond:64000}:undefined);recorder.current=capture;const parts:BlobPart[]=[];let bytes=0;
   capture.ondataavailable=event=>{if(event.data.size){parts.push(event.data);bytes+=event.data.size;if(bytes>10_000_000&&capture.state==='recording')capture.stop()}};
   capture.onerror=()=>{if(mounted.current){setError('Audio recording failed. No audio was uploaded.');setActive(null)}input.getTracks().forEach(track=>track.stop())};
   capture.onstop=()=>{input.getTracks().forEach(track=>track.stop());if(recordTimer.current)clearTimeout(recordTimer.current);if(mounted.current){const type=capture.mimeType||mime||'audio/webm';const blob=new Blob(parts,{type});if(blob.size)setAudio({url:URL.createObjectURL(blob),extension:type.includes('mp4')?'m4a':type.includes('ogg')?'ogg':'webm'});setActive(null);setStatus('Recording ready on this device. No transcript was generated and no audio was uploaded.')}};
   capture.start(1000);setActive('audio');setStatus('Recording on this device. Stops automatically after two minutes.');recordTimer.current=setTimeout(()=>{if(capture.state==='recording')capture.stop()},120000);
  }catch{setError('Microphone permission was denied or no recording device is available. Type your observation instead.');setStatus('')}
  finally{if(mounted.current)setRequesting(false)}
 }
 function append(){if(!draft.trim()||disabled||active)return;try{onAppend(draft.trim());setDraft('');setError('');setStatus('Added to your editable note draft. Save the sample record to keep it.')}catch(reason:any){setError(reason.message||'The note could not be added. Your draft is kept; try again after the sample record loads.')}}
 return <section className="voice-notes" aria-label="Voice notes">
  <div className="voice-heading"><Mic size={18}/><div><h3>Speak an observation</h3><p>Keep your hands on the specimen; review the words before saving.</p></div></div>
  {speechAvailable?<><label className="voice-consent"><input type="checkbox" checked={consent} disabled={!!active} onChange={event=>setConsent(event.target.checked)}/><span>I understand that browser speech-to-text may send audio to the browser vendor's service. REEFPRINT does not control that service or claim offline transcription.</span></label><div className="voice-controls"><button type="button" className="button" disabled={disabled||!!active||requesting||!consent} onClick={dictate}><Mic size={15}/>Start dictation</button>{active==='speech'&&<button type="button" className="button" onClick={stop}><Square size={15}/>Stop dictation</button>}</div></>:<p className="voice-disclosure">Speech-to-text is unavailable in this browser. You can type a draft{recordAvailable?' or record a voice memo on this device':''}. Audio recording does not create a transcript.</p>}
  {recordAvailable&&<div className="voice-controls"><button type="button" className="button" disabled={disabled||!!active||requesting} onClick={recordAudio}><Mic size={15}/>{requesting?'Requesting microphone…':'Record local voice memo'}</button>{active==='audio'&&<button type="button" className="button" onClick={stop}><Square size={15}/>Stop recording</button>}<span className="voice-disclosure">No recording is uploaded. Download it to keep it.</span></div>}
  {audio&&<div className="voice-playback"><audio controls src={audio.url} aria-label="Recorded voice memo"/><a className="button" href={audio.url} download={'reefprint-voice-note.'+audio.extension}><Download size={15}/>Download voice memo</a></div>}
  <label className="voice-draft">Review transcript or type a draft<textarea value={draft} maxLength={8000} rows={3} disabled={disabled||!!active} onChange={event=>setDraft(event.target.value)} placeholder="For example: reflected-light acquisition; fine sulphide intergrowths observed. Check spellings and units."/></label>
  {interim&&<p className="voice-interim" aria-live="polite">Heard, still being transcribed: {interim}</p>}
  {status&&<p className="voice-status" role="status">{status}</p>}
  {error&&<p className="voice-error" role="alert"><AlertCircle size={15}/>{error}</p>}
  <button type="button" className="button" disabled={disabled||!!active||!draft.trim()} onClick={append}><FilePlus size={15}/>Add to note draft</button>
 </section>
}
