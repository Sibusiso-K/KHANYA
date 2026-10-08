import {test,expect,type Page} from '@playwright/test';

async function mockWorkspace(page:Page,providerReady=false){
 const calls:{path:string;method:string;body:any}[]=[];
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;let body:any={};
  let payload:any=null;try{payload=request.postDataJSON()}catch{}
  calls.push({path,method:request.method(),body:payload});
  if(path==='/api/config')body={auth_required:false,cloud_sync:false};
  else if(path==='/api/samples')body=[{id:'test_11',thumbnail_url:'',dimensions:[512,512],dataset:'Held-out S2',has_prediction:false}];
  else if(path==='/api/report')body={model_sha:'fixture',checkpoint_available:true,checkpoint_matches_report:false,report_source:'fixture',metrics:null,limitations:[],download_url:'/api/report/download'};
  else if(path==='/api/health')body={status:'ok',checkpoint_available:true,model_sha:'fixture',model_approved:true};
  else if(path==='/api/samples/test_11/record')body={sample_id:'test_11',version:request.method()==='PUT'?1:0,updated_at:null,record:request.method()==='PUT'?payload.record:{}};
  else if(path==='/api/samples/test_11')body={id:'test_11',result_id:null,raw_url:'',phases:[],verified:true};
  else if(path==='/api/assistant/status')body={local_available:true,provider_ready:providerReady,provider:providerReady?'featherless':null,model:providerReady?'fixture-model':null,context_policy:'Question and bounded report facts only'};
  else if(path==='/api/assistant'){
   const note=payload.question.startsWith('Add note:');
   body={answer:note?'Review the note; it changes the draft only.':'No report matches the active checkpoint. Inspect provenance before claiming accuracy.',mode:payload.use_provider?'provider':'local-evidence',evidence:[{label:'Control scope',kind:'simulated',value:'Local simulator only'}],warnings:['No task runs until you approve it.'],proposals:[note?{id:'addNote',action:'addNote',label:'Add to note draft',args:{note:payload.question.slice(9).trim()}}:{id:'openReports',action:'openReports',label:'Open accuracy evidence',args:{}}]};
  }
  await route.fulfill({json:body});
 });
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'From specimen to insight'})).toBeVisible();
 return calls;
}

test('assistant proposals need approval and notes remain unsaved at mobile size',async({page})=>{
 await page.setViewportSize({width:375,height:812});
 const calls=await mockWorkspace(page);
 await page.getByRole('button',{name:'Open research assistant'}).click();
 const drawer=page.getByRole('complementary',{name:'Research assistant drawer'});
 await expect(drawer.getByRole('heading',{name:'Ask the evidence'})).toBeVisible();
 await drawer.getByLabel('Your question').fill('Add note: Fine sulphide intergrowths; verify the overlay.');
 await drawer.getByRole('button',{name:'Ask about this sample'}).click();
 await expect(drawer.getByRole('button',{name:'Add to note draft'})).toBeVisible();
 expect(calls.filter(call=>call.method==='PUT')).toHaveLength(0);
 await expect(page.getByRole('textbox',{name:'Field notes',exact:true})).toHaveCount(0);
 await drawer.getByRole('button',{name:'Add to note draft'}).click();
 await expect(drawer.getByText('Added to editable draft; save the sample record to keep it.')).toBeVisible();
 await page.keyboard.press('Escape');
 await expect(page.getByRole('textbox',{name:'Field notes',exact:true})).toHaveValue('Fine sulphide intergrowths; verify the overlay.');
 expect(calls.filter(call=>call.method==='PUT')).toHaveLength(0);
 await page.getByRole('button',{name:'Save sample record',exact:true}).click();
 await expect(page.getByRole('button',{name:'Saved on server',exact:true})).toBeVisible();
 expect(calls.filter(call=>call.method==='PUT')).toHaveLength(1);
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('speech consent and explicit start produce a reviewable draft, without automatic save',async({page})=>{
 // Controlled browser fixture: verifies UI flow, not real microphone/service accuracy.
 await page.addInitScript(()=>{
  (window as any).SpeechRecognition=class{
   lang='';continuous=false;interimResults=false;onresult:any;onerror:any;onend:any;
   start(){setTimeout(()=>{this.onresult?.({resultIndex:0,results:[{isFinal:true,0:{transcript:'Pentlandite under reflected light'}}]});this.onend?.()},20)}
   stop(){this.onend?.()}abort(){}
  };
 });
 const calls=await mockWorkspace(page);
 await page.getByRole('button',{name:'Sample record & field notes'}).click();
 const voice=page.getByRole('region',{name:'Voice notes'});
 await expect(voice.getByRole('button',{name:'Start dictation'})).toBeDisabled();
 await voice.getByRole('checkbox').check();
 await voice.getByRole('button',{name:'Start dictation'}).click();
 await expect(voice.getByLabel('Review transcript or type a draft')).toHaveValue('Pentlandite under reflected light');
 await voice.getByLabel('Review transcript or type a draft').fill('Pentlandite suspected; review spelling and overlay.');
 await voice.getByRole('button',{name:'Add to note draft'}).click();
 await expect(page.getByRole('textbox',{name:'Field notes',exact:true})).toHaveValue('Pentlandite suspected; review spelling and overlay.');
 expect(calls.filter(call=>call.method==='PUT')).toHaveLength(0);
});

test('provider connection is opt-in and assistant navigation is explicitly approved',async({page})=>{
 await page.setViewportSize({width:1440,height:1000});
 const calls=await mockWorkspace(page,true);
 await page.getByRole('button',{name:'Open research assistant'}).click();
 const drawer=page.getByRole('complementary',{name:'Research assistant drawer'});
 await drawer.getByText('Language model connection',{exact:true}).click();
 await drawer.getByRole('checkbox',{name:'Use the configured language model'}).check();
 await drawer.getByLabel('Your question').fill('How accurate is the model?');
 await expect(drawer.getByRole('button',{name:'Ask about this sample'})).toBeDisabled();
 expect(calls.filter(call=>call.path==='/api/assistant')).toHaveLength(0);
 await drawer.getByRole('checkbox',{name:/Share this question/}).check();
 await drawer.getByRole('button',{name:'Ask about this sample'}).click();
 await expect(drawer.getByText('Generated explanation',{exact:true})).toBeVisible();
 const request=calls.find(call=>call.path==='/api/assistant')!;
 expect(request.body.context_opt_in).toBe(true);expect(request.body.use_provider).toBe(true);
 expect(Object.keys(request.body).sort()).toEqual(['context_opt_in','question','result_id','sample_id','use_provider']);
 await expect(page.getByRole('heading',{name:'From specimen to insight'})).toBeVisible();
 await drawer.getByRole('button',{name:'Open accuracy evidence'}).click();
 await expect(page.getByRole('heading',{name:'Evidence you can inspect'})).toBeVisible();
 await page.keyboard.press('Escape');
 await expect(page.getByRole('button',{name:'Open research assistant'})).toBeFocused();
});
