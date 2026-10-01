import {test,expect,type Page} from '@playwright/test';

async function mockWorkspace(page:Page){
 const mutations:string[]=[];
 await page.route('**/api/**',async route=>{
  const request=route.request(),path=new URL(request.url()).pathname;
  if(request.method()!=='GET')mutations.push(path);
  let body:any={};
  if(path==='/api/config')body={auth_required:false,cloud_sync:false};
  else if(path==='/api/samples')body=[{id:'test_11',thumbnail_url:'',dimensions:[512,512],dataset:'S2 fixture',has_prediction:false}];
  else if(path==='/api/report')body={model_sha:'fixture-active-sha',model_approved:false,approved_model_sha:'fixture-approved-sha',metrics:null,limitations:[],download_url:'/api/report/download'};
  else if(path==='/api/health')body={checkpoint_available:true,model_sha:'fixture-active-sha',model_approved:false,approved_model_sha:'fixture-approved-sha',model_ready:true,cloud_sync:false,deployment:'local'};
  else if(path==='/api/samples/test_11/record')body={sample_id:'test_11',version:0,updated_at:null,record:{}};
  else if(path==='/api/samples/test_11')body={id:'test_11',result_id:null,raw_url:'',phases:[],verified:true};
  else if(path==='/api/assistant/status')body={local_available:true,provider_ready:false,provider:null,model:null,context_policy:'Question and bounded result/report facts only; no images, audio, notes or coordinates.'};
  await route.fulfill({json:body});
 });
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'From specimen to insight'})).toBeVisible();
 return mutations;
}

test('appearance persists for the current workspace without changing model data',async({page})=>{
 await page.setViewportSize({width:1440,height:960});
 await page.addInitScript(()=>{if(!localStorage.getItem('theme-fixture-initialized')){localStorage.setItem('reefprint-local-appearance','field-paper');localStorage.setItem('reefprint-another-account-appearance','mineral-night');localStorage.setItem('theme-fixture-initialized','true')}});
 const mutations=await mockWorkspace(page);
 await expect(page.locator('html')).toHaveAttribute('data-reef-theme','field-paper');
 const colours=await page.locator('.legend i').evaluateAll(elements=>elements.map(element=>getComputedStyle(element).backgroundColor));
 await page.getByRole('navigation').getByRole('button',{name:'Settings',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Workspace settings',exact:true})).toBeVisible();
 await expect(page.getByText('fixture-active-sha',{exact:true})).toBeVisible();
 await expect(page.getByText('Local CPU on the analysis server',{exact:true})).toBeVisible();
 await expect(page.getByText('Local evidence helper available',{exact:true})).toBeVisible();
 await page.getByRole('radio',{name:/Mineral night/}).check();
 await expect(page.locator('html')).toHaveAttribute('data-reef-theme','mineral-night');
 await expect(page.getByText('Appearance saved on this browser for this account.')).toBeVisible();
 await page.reload();
 await expect(page.getByRole('heading',{name:'From specimen to insight'})).toBeVisible();
 await expect(page.locator('html')).toHaveAttribute('data-reef-theme','mineral-night');
 expect(await page.locator('.legend i').evaluateAll(elements=>elements.map(element=>getComputedStyle(element).backgroundColor))).toEqual(colours);
 expect(await page.evaluate(()=>localStorage.getItem('reefprint-another-account-appearance'))).toBe('mineral-night');
 expect(mutations).toEqual([]);
});

test('mobile themes retain contrast, keyboard choice and read-only assistant setup',async({page})=>{
 await page.setViewportSize({width:375,height:812});
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.addInitScript(()=>{localStorage.setItem('reefprint-local-appearance','invalid-theme');localStorage.setItem('reefprint-another-account-appearance','mineral-night')});
 await mockWorkspace(page);
 await expect(page.locator('html')).toHaveAttribute('data-reef-theme','workbench');
 await page.getByRole('navigation').getByRole('button',{name:'Settings',exact:true}).click();
 for(const theme of ['White workbench','Mineral night','Field paper']){
  await page.getByRole('radio',{name:new RegExp(theme)}).check();
  const metrics=await page.evaluate(()=>{
   const panel=document.querySelector('.settings-appearance')!,text=document.querySelector('.settings-help')!;
   const rgb=(value:string)=>value.match(/[\d.]+/g)!.slice(0,3).map(Number);
   const luminance=(values:number[])=>values.map(value=>{const n=value/255;return n<=.04045?n/12.92:((n+.055)/1.055)**2.4}).reduce((sum,value,index)=>sum+value*[.2126,.7152,.0722][index],0);
   const a=luminance(rgb(getComputedStyle(panel).backgroundColor)),b=luminance(rgb(getComputedStyle(text).color));
   return {contrast:(Math.max(a,b)+.05)/(Math.min(a,b)+.05),overflow:document.documentElement.scrollWidth>innerWidth,wide:[...document.querySelectorAll<HTMLElement>('body *')].filter(el=>el.getBoundingClientRect().right>innerWidth+1).map(el=>({tag:el.tagName,cls:el.className,rect:el.getBoundingClientRect().toJSON()}))};
  });
  expect(metrics.contrast,theme+' body text contrast').toBeGreaterThanOrEqual(4.5);
  expect(metrics.overflow,theme+' mobile page overflow '+JSON.stringify(metrics.wide)).toBe(false);
 }
 const radio=page.getByRole('radio',{name:/White workbench/});
 await radio.focus();await page.keyboard.press('Space');
 await expect(page.locator('html')).toHaveAttribute('data-reef-theme','workbench');
 await page.getByText('Connect your own language model privately',{exact:true}).click();
 await expect(page.getByText('.workbench/cloud.env',{exact:true})).toBeVisible();
 await expect(page.locator('input[type="password"]')).toHaveCount(0);
 await expect(page.locator('.workbench-session')).toHaveCSS('animation-name','none');
});

test('signed-out appearance and login motion stay separate from another account',async({page})=>{
 await page.setViewportSize({width:375,height:812});
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.addInitScript(()=>{localStorage.setItem('reefprint-signed-out-appearance','field-paper');localStorage.setItem('reefprint-other-user-appearance','mineral-night')});
 await page.route('**/api/config',route=>route.fulfill({json:{auth_required:true,cloud_sync:true,supabase_url:'https://fixture.supabase.co',supabase_publishable_key:'sb_publishable_fixture'}}));
 await page.goto('/');
 await expect(page.getByRole('heading',{name:'Sign in to your workspace'})).toBeVisible();
 await expect(page.locator('html')).toHaveAttribute('data-reef-theme','field-paper');
 await expect(page.getByRole('button',{name:'Sign in and open workspace'})).toBeVisible();
 await expect(page.getByRole('button',{name:'Create a private account'})).toBeVisible();
 await expect(page.locator('.reef-brand-upper')).toHaveCSS('animation-name','none');
 expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
});
