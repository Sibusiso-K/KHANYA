import {test,expect} from '@playwright/test';
test('scan screen displays actual job counts and reduced-motion mode',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;
  let body:any={};
  if(path==='/api/config')body={auth_required:false,cloud_sync:false};
  if(path==='/api/health')body={checkpoint_available:true,status:'ok'};
  if(path==='/api/report')body={model_sha:'test',metrics:null,limitations:[]};
  if(path==='/api/samples')body=[{id:'test_11',dimensions:[1600,1100],dataset:'Fixture',has_prediction:false,thumbnail_url:''}];
  if(path==='/api/samples/test_11')body={id:'test_11',raw_url:'',result_id:null,phases:[],verified:true};
  if(path.endsWith('/record'))body={version:0,record:{}};
  if(path==='/api/inferences')body={id:'scan-job',status:'queued'};
  if(path==='/api/jobs/scan-job')body={id:'scan-job',status:'running',progress:{stage:'segmenting',completed:2,total:6}};
  await route.fulfill({json:body});
 });
 await page.goto('/');
 await page.getByRole('button',{name:/Run analysis/i}).first().click();
 await expect(page.getByLabel('Analysis in progress')).toBeVisible();
 await expect(page.getByText('2 / 6 fields classified',{exact:true})).toBeVisible();
 await expect(page.getByRole('progressbar')).toHaveAttribute('value','2');
 expect(await page.locator('.scan-beam').evaluate(el=>getComputedStyle(el).animationName)).toBe('none');
 await page.screenshot({path:'test-results/analysis-scanning-desktop.png'});
 await page.setViewportSize({width:375,height:812});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/analysis-scanning-mobile.png'});
});
