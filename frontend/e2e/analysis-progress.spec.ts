import {test,expect} from '@playwright/test';
test('live analysis uses completed predictions, native counts and transparent unknown areas',async({page})=>{
 await page.setViewportSize({width:1440,height:1100});
 await page.emulateMedia({reducedMotion:'reduce'});
 const original='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100"><rect width="1600" height="1100" fill="#657079"/><text x="500" y="300" fill="white" font-size="32">UI test image fixture</text></svg>');
 await page.route('**/api/**',async route=>{
  const path=new URL(route.request().url()).pathname;let body:any={};
  if(path==='/api/config')body={auth_required:false,cloud_sync:false};
  if(path==='/api/health')body={checkpoint_available:true,status:'ok',model_approved:true};
  if(path==='/api/report')body={model_sha:'test',metrics:null,limitations:[]};
  if(path==='/api/samples')body=[{id:'test_11',dimensions:[1600,1100],dataset:'Fixture',has_prediction:false,thumbnail_url:original}];
  if(path==='/api/samples/test_11')body={id:'test_11',raw_url:original,result_id:null,phases:[],verified:true};
  if(path.endsWith('/record'))body={version:0,record:{}};
  if(path==='/api/inferences')body={id:'scan-job',status:'queued'};
  if(path==='/api/jobs/scan-job')body={id:'scan-job',status:'running',progress:{stage:'segmenting',completed:2,total:6,box:[512,0,1024,512],image_size:[1600,1100],evidence:{revision:2,preview_url:'/api/jobs/scan-job/preview?revision=2',preview_size:[768,528],analysed_pixels:524288,image_pixels:1760000,coverage_fraction:524288/1760000,phases:[{name:'chalcopyrite',color:'#f28136',pixels:262144,area_pct:50},{name:'pyrrhotite',color:'#119eae',pixels:262144,area_pct:50}],provisional:true,basis:'analysed pixels only'}}};
  if(path.endsWith('/preview')){await route.fulfill({contentType:'image/svg+xml',body:'<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1100"><rect width="512" height="512" fill="#f28136" fill-opacity=".75"/><rect x="512" width="512" height="512" fill="#119eae" fill-opacity=".75"/></svg>'});return}
  await route.fulfill({json:body});
 });
 await page.goto('/');await page.getByRole('button',{name:/Run analysis/i}).first().click();
 await expect(page.getByLabel('Live pixel analysis')).toBeVisible();
 await expect(page.getByText('2 of 6 fields completed',{exact:true})).toBeVisible();
 await expect(page.getByText('524,288 pixels · 29.8% of image',{exact:true})).toBeVisible();
 await expect(page.getByRole('progressbar')).toHaveAttribute('value','2');
 await expect(page.getByAltText('Live model predictions on analysed fields; clear areas are unanalysed')).toBeVisible();
 await expect(page.locator('.live-field-bounds rect')).toHaveAttribute('x','512');
 await expect(page.locator('.scan-beam')).toHaveCount(0);
 await expect(page.getByText('Sampled pixel composition',{exact:true})).toBeVisible();
 await page.screenshot({path:'test-results/analysis-actual-fields-desktop.png'});
 await page.setViewportSize({width:375,height:812});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'test-results/analysis-actual-fields-mobile.png',fullPage:true});
});
