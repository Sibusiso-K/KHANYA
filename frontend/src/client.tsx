import {useEffect,useState,type ImgHTMLAttributes,type ReactNode} from 'react';
import {createClient,type SupabaseClient,type Session} from '@supabase/supabase-js';

type Config={auth_required:boolean;supabase_url:string|null;supabase_publishable_key:string|null;cloud_sync:boolean};
let client:SupabaseClient|null=null;
let configuration:Config|null=null;
let accountId='local';
export function workspaceStorageKey(key:string){return 'reefprint-'+accountId+'-'+key;}
export async function api<T>(path:string,options?:RequestInit):Promise<T>{
  const headers=new Headers(options?.headers);
  if(client){const {data,error}=await client.auth.getSession();if(error)throw error;if(data.session)headers.set('Authorization','Bearer '+data.session.access_token);}
  const response=await fetch('/api'+path,{...options,headers});
  if(!response.ok){let error:any;try{error=await response.json()}catch{error={detail:response.statusText}}
    throw Error(Array.isArray(error.detail)?error.detail.map((item:any)=>item.loc?.slice(1).join('.')+': '+item.msg).join('; '):error.detail||'Request failed');}
  return response.json();
}
export async function authenticatedMedia(src:string):Promise<string>{
  if(!src.startsWith('/api/')||!configuration?.auth_required)return src;
  const {data,error}=await client!.auth.getSession();if(error)throw error;
  if(!data.session)throw Error('Sign in to view this image.');
  const response=await fetch(src,{headers:{Authorization:'Bearer '+data.session.access_token}});
  if(!response.ok)throw Error('Image could not load ('+response.status+').');
  return URL.createObjectURL(await response.blob());
}
export async function authenticatedDownload(src:string,name:string){
  const url=await authenticatedMedia(src);const link=document.createElement('a');link.href=url;link.download=name;link.click();
  if(url.startsWith('blob:'))setTimeout(()=>URL.revokeObjectURL(url),1000);
}
export function AuthImage({src,...props}:ImgHTMLAttributes<HTMLImageElement>){
  const [url,setUrl]=useState<string>();const [failed,setFailed]=useState(false);
  useEffect(()=>{let alive=true;let owned:string|undefined;setUrl(undefined);setFailed(false);
    if(src)authenticatedMedia(src).then(value=>{owned=value;if(alive)setUrl(value);else if(value.startsWith('blob:'))URL.revokeObjectURL(value)}).catch(()=>{if(alive)setFailed(true)});
    return()=>{alive=false;if(owned?.startsWith('blob:'))URL.revokeObjectURL(owned)};
  },[src]);
  return failed?<span role="status">Image unavailable</span>:<img {...props} src={url}/>;
}
export function AuthGate({children}:{children:ReactNode}){
  const [config,setConfig]=useState<Config|null>(null),[session,setSession]=useState<Session|null>(null),[ready,setReady]=useState(false);
  const [email,setEmail]=useState(''),[password,setPassword]=useState(''),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  async function register(){setBusy(true);setError('');try{if(!email||password.length<8)throw Error('Enter an email and a password of at least 8 characters.');const {error}=await client!.auth.signUp({email,password,options:{emailRedirectTo:new URL("/",window.location.origin).href}});if(error)throw error;setError('Check your email to confirm your account, then return here to sign in.')}catch(reason:any){setError(reason.message)}finally{setBusy(false)}}
  useEffect(()=>{let alive=true;let dispose:(()=>void)|undefined;
    fetch('/api/config').then(async response=>{if(!response.ok)throw Error('Backend configuration unavailable.');return response.json()}).then(async (value:Config)=>{configuration=value; if(!alive)return;setConfig(value);
      if(value.auth_required){if(!value.supabase_url||!value.supabase_publishable_key)throw Error('Cloud login configuration is incomplete.');client=createClient(value.supabase_url,value.supabase_publishable_key);
        const {data,error}=await client.auth.getSession();if(error)throw error;if(alive){accountId=data.session?.user.id||'signed-out';setSession(data.session);}
        const subscription=client.auth.onAuthStateChange((_event,next)=>{if(alive){accountId=next?.user.id||'signed-out';setSession(next)}});dispose=()=>subscription.data.subscription.unsubscribe();}
      if(alive)setReady(true);
    }).catch(reason=>{if(alive)setError(reason.message)});
    return()=>{alive=false;dispose?.()};
  },[]);
  async function login(event:React.FormEvent){event.preventDefault();setBusy(true);setError('');try{const {error}=await client!.auth.signInWithPassword({email,password});if(error)throw error;setPassword('')}catch(reason:any){setError(reason.message)}finally{setBusy(false)}}
  if(!ready)return <main className="auth-shell"><h1>REEFPRINT / KHANYA</h1><p role="status">{error||'Connecting to your workspace…'}</p><button className="button" onClick={()=>location.reload()}>Retry connection</button></main>;
  if(config?.auth_required&&!session)return <main className="auth-shell"><div className="auth-introduction"><p>REEFPRINT / KHANYA</p><h1>One sample.<br/>A clearer decision.</h1><p>Inspect mineral phases, trace the evidence and test a processing scenario in your private research workspace.</p></div><form onSubmit={login} className="panel auth-form"><h2>Sign in to your workspace</h2><p>Use your REEFPRINT Supabase account.</p><label>Email<input required autoComplete="username" type="email" value={email} onChange={event=>setEmail(event.target.value)}/></label><label>Password<input required autoComplete="current-password" type="password" value={password} onChange={event=>setPassword(event.target.value)}/></label>{error&&<p role="alert">{error}</p>}<button className="button primary" disabled={busy}>{busy?'Signing in…':'Open workspace'}</button><button className="button" type="button" disabled={busy} onClick={register}>Create a private workspace</button><p>Confirm your email before signing in. Each account has its own sample records.</p></form></main>;
  return <>{session&&<div className="account-strip"><span>{session.user.email} · Private workspace</span><button className="text-button" onClick={()=>client!.auth.signOut()}>Sign out</button></div>}<div key={session?.user.id||'local'}>{children}</div></>;
}


