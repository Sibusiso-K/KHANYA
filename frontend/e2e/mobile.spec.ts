import {test, expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

test('all workbench pages remain legible and unclipped at 375px', async ({page}) => {
  await page.route('**/api/**', async route => {
    const url = route.request().url();
    let body: unknown = {};
    if (url.endsWith('/api/samples')) body = [{id:'test_11',thumbnail_url:'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=',dimensions:[512,512],dataset:'Held-out S2',has_prediction:false}];
    if (url.endsWith('/api/report')) body = {model_sha:'abc',checkpoint_available:false,checkpoint_matches_report:false,report_source:'test',metrics:null,limitations:[],download_url:''};
    if (url.endsWith('/api/health')) body = {status:'ok',checkpoint_available:false};
    if (url.endsWith('/api/samples/test_11/record')) body = {sample_id:'test_11',version:0,updated_at:null,record:{}};
    if (url.endsWith('/api/samples/test_11')) body = {id:'test_11',result_id:null,raw_url:'',phases:[],verified:true};
    await route.fulfill({json:body});
  });
  await page.goto('/');
  await expect(page.getByRole('heading', {name:'From specimen to insight'})).toBeVisible();
  const pages = ['Samples','Spatial','Process','Reports'];
  for (const name of pages) {
    await page.getByRole('navigation').getByRole('button', {name, exact:true}).click();
    await expect(page.getByRole('heading', {level:1})).toBeVisible();
    await page.waitForTimeout(name === 'Spatial' ? 800 : 100);
    const check = await page.evaluate(() => {
      const visible = [...document.querySelectorAll<HTMLElement>('body *')].filter(el => {
        const s=getComputedStyle(el),r=el.getBoundingClientRect(); return !!el.textContent?.trim() && s.display!=='none' && s.visibility!=='hidden' && r.width>0 && r.height>0;
      });
      return {overflow:document.documentElement.scrollWidth>innerWidth,wide:[...document.querySelectorAll<HTMLElement>('body *')].map(el=>({tag:el.tagName,cls:el.className,scroll:el.scrollWidth,width:el.clientWidth,rect:el.getBoundingClientRect().toJSON()})).filter(x=>x.scroll>x.width+1||x.rect.right>innerWidth+1),small:visible.filter(el=>parseFloat(getComputedStyle(el).fontSize)<12).map(el=>({tag:el.tagName,text:el.textContent?.trim().slice(0,50),size:getComputedStyle(el).fontSize}))};
    });
    expect(check.overflow, `${name} horizontal overflow ${JSON.stringify(check.wide)}`).toBe(false);
    expect(check.small, `${name} text smaller than 12px`).toEqual([]);
    if (name === 'Spatial') {
      await expect(page.getByRole('heading', {name:'No survey imported'})).toBeVisible();
      await expect(page.getByText('SYNTHETIC · NOT DATA')).toHaveCount(0);
      await page.getByRole('checkbox', {name:'Show synthetic demo scene (not real data)'}).check();
      await expect(page.getByText('SYNTHETIC · NOT DATA')).toBeVisible();
    }
  }
});

test('Quick result grain click selects the exact API grain id', async ({page}) => {
  const png=await readFile(new URL('./fixtures/grain-ids.png', import.meta.url));
  const report={n_grains:1,n_payload_grains:1,grains:[{id:7,area_px:262144,ecd_px:577.4,phases:{chalcopyrite:1},payload_fraction:1,liberated:true,bbox:[0,0,511,511]}],weight_percent:{chalcopyrite:100},association:{chalcopyrite:{resin:1}},liberation_by_size:[{from_px:0,to_px:16,payload_grains:0,payload_area_px:0,liberated_share:null},{from_px:16,to_px:32,payload_grains:0,payload_area_px:0,liberated_share:null},{from_px:32,to_px:64,payload_grains:0,payload_area_px:0,liberated_share:null},{from_px:64,to_px:128,payload_grains:0,payload_area_px:0,liberated_share:null},{from_px:128,to_px:256,payload_grains:0,payload_area_px:0,liberated_share:null},{from_px:256,to_px:null,payload_grains:1,payload_area_px:262144,liberated_share:1}],microns_per_pixel:null};
  const result={id:'test_11',result_id:'rid-1',prediction_source:'fresh',phases:[{name:'background',area_pct:0,color:'#8c96a1'},{name:'chalcopyrite',area_pct:100,color:'#f28136'}],confidence:.9,advisory:{action:'Grind finer',reason:'measured'},model_sha:'abc',elapsed_seconds:1,raw_url:'/api/samples/test_11/image?layer=raw&result_id=rid-1',mask_url:'/api/samples/test_11/image?layer=mask&result_id=rid-1',overlay_url:null,verified:true,mode:'field'};
  await page.route('**/api/**', async route=>{
    const url=new URL(route.request().url()),path=url.pathname;
    if(path==='/api/samples'){return route.fulfill({json:[{id:'test_11',thumbnail_url:'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=',dimensions:[512,512],dataset:'LumenStone S2 test',has_prediction:false}]})}
    if(path==='/api/report')return route.fulfill({json:{model_sha:'abc',checkpoint_available:true,checkpoint_matches_report:true,report_source:'test',metrics:null,limitations:[],download_url:''}});
    if(path==='/api/health')return route.fulfill({json:{status:'ok',checkpoint_available:true,model_sha:'abc'}});
    if(path==='/api/samples/test_11/record')return route.fulfill({json:{sample_id:'test_11',version:0,updated_at:null,record:{}}});
    if(path==='/api/samples/test_11')return route.fulfill({json:{id:'test_11',result_id:null,prediction_source:'unavailable',phases:[],raw_url:'',mask_url:null,verified:true}});
    if(path==='/api/inferences')return route.fulfill({status:202,json:{id:'job-1',status:'queued'}});
    if(path==='/api/jobs/job-1')return route.fulfill({json:{id:'job-1',status:'complete',result}});
    if(path==='/api/results/rid-1/grains')return route.fulfill({json:report});
    if(path==='/api/results/rid-1/grain-ids.png')return route.fulfill({status:200,contentType:'image/png',body:png});
    if(path==='/api/samples/test_11/image')return route.fulfill({status:200,contentType:'image/png',body:png});
    return route.fulfill({json:{}});
  });
  await page.goto('/');
  await page.getByRole('button',{name:'Run analysis'}).first().click();
  await expect(page.getByText('1 advisor-matched grains')).toBeVisible({timeout:10000});
  await expect(page.getByText(/Tap or click a grain/)).toBeVisible();
  const image=page.getByAltText('Model-predicted mineral phase segmentation');
  expect((await image.boundingBox())?.width||0).toBeGreaterThan(300);
  await image.click();
  await expect(page.getByRole('heading',{name:'Grain 7'})).toBeVisible();
  await expect(page.getByText(/Equivalent circle diameter: 577.4 px/)).toBeVisible();
  await expect(page.getByText('FREE',{exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Composition',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Mineral contacts',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Liberation by grain size',exact:true})).toBeVisible();
  const mobileEvidence=await page.evaluate(()=>({overflow:document.documentElement.scrollWidth>innerWidth,small:[...document.querySelectorAll<HTMLElement>('.grain-evidence *')].filter(el=>el.textContent?.trim()&&parseFloat(getComputedStyle(el).fontSize)<12).map(el=>el.textContent?.trim())}));
  expect(mobileEvidence.overflow).toBe(false);
  expect(mobileEvidence.small).toEqual([]);
});
