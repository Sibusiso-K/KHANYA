import {test, expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';

const fixture = {type:'FeatureCollection',features:[
  {type:'Feature',properties:{id:'SURVEY-A',sample_id:'test_11',depth_m:120},geometry:{type:'Point',coordinates:[28,-26,1500]}},
  {type:'Feature',properties:{id:'SURVEY-B',sample_id:'test_01',depth_m:90},geometry:{type:'Point',coordinates:[28.002,-25.999,1490]}},
]};

test('survey import links image IDs, map query and corridor filtering without fabricating geology', async ({page}) => {
  test.setTimeout(90_000);
  const external:string[]=[];
  const origin=new URL(test.info().project.use.baseURL as string).origin;
  page.on('request',req=>{const url=new URL(req.url());if(['http:','https:'].includes(url.protocol)&&url.origin!==origin)external.push(req.url());});
  await page.route('**/api/**', async route => {
    const path=new URL(route.request().url()).pathname;
    let body:unknown={};
    if(path==='/api/config')body={auth_required:false,cloud_sync:false};
    if(path==='/api/samples')body=['test_11','test_01'].map(id=>({id,thumbnail_url:'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=',dimensions:[512,512],dataset:'Explicit browser-test fixture',has_prediction:false}));
    if(path==='/api/report')body={model_sha:'test-fixture',checkpoint_available:false,checkpoint_matches_report:false,metrics:null,limitations:[],download_url:''};
    if(path==='/api/health')body={status:'ok',checkpoint_available:false};
    if(path.endsWith('/record'))body={version:0,record:{}};
    if(/^\/api\/samples\/test_\d+$/.test(path))body={id:path.split('/').at(-1),result_id:null,raw_url:'',phases:[],verified:true};
    return route.fulfill({json:body});
  });
  await page.goto('/',{waitUntil:'domcontentloaded'});
  await page.getByRole('navigation').getByRole('button',{name:'Spatial',exact:true}).click();
  await expect(page.getByRole('heading',{name:'No survey imported'})).toBeVisible();
  await expect(page.getByRole('checkbox',{name:'Show synthetic demo scene (not real data)'})).not.toBeChecked();
  await page.locator('input[type=file][accept=".geojson,.json"]').setInputFiles({name:'explicit-test-survey.geojson',mimeType:'application/geo+json',buffer:Buffer.from(JSON.stringify(fixture))});
  await expect(page.locator('.geo-inspector').getByRole('heading',{name:'SURVEY-A',exact:true})).toBeVisible();
  await page.getByRole('button',{name:'Plan map',exact:true}).click();
  await expect(page.locator('.survey-map-tools')).toContainText('Survey map');
  const map=page.getByRole('img',{name:/Interactive plan map/});
  const box=await map.boundingBox();if(!box)throw Error('Map viewport absent');
  await map.hover({position:{x:box.width*.5,y:box.height*.5}});
  await expect(page.locator('.survey-map-status')).toContainText(/° S \/ .*° E/);
  const before=await page.locator('[data-map-point="SURVEY-A"] circle').last().getAttribute('cx');
  await page.getByRole('button',{name:'Zoom map in'}).click();
  expect(await page.locator('[data-map-point="SURVEY-A"] circle').last().getAttribute('cx')).not.toBe(before);
  await page.getByRole('button',{name:'Fit all survey points'}).click();
  await page.locator('[data-map-point="SURVEY-B"] circle').last().click();
  await expect(page.locator('.geo-inspector').getByRole('heading',{name:'SURVEY-B',exact:true})).toBeVisible();
  await expect(page.locator('.geo-properties')).toContainText('28.002000');
  await expect(page.locator('.geo-sample-preview')).toContainText('test_01');
  await page.setViewportSize({width:1440,height:1000});
  await page.screenshot({path:test.info().outputPath('survey-map-desktop-fixture.png'),fullPage:true});
  await page.getByRole('button',{name:'E–W section',exact:true}).click();
  await expect(page.locator('.survey-section-header')).toContainText('2 / 2 records in corridor');
  await page.getByLabel('Section corridor width').fill('10');
  await page.getByLabel('Section north centre').focus();
  await page.keyboard.press('Home');
  await expect(page.locator('.survey-section-header')).toContainText('1 / 2 records in corridor');
  await expect(page.getByText(/outside corridor/).first()).toBeVisible();
  await page.screenshot({path:test.info().outputPath('survey-section-desktop-fixture.png'),fullPage:true});
  await page.setViewportSize({width:375,height:812});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)).toBe(false);
  await page.screenshot({path:test.info().outputPath('survey-section-mobile-fixture.png'),fullPage:true});
  const exportedPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export survey',exact:true}).click();const exported=await exportedPromise;
  const path=await exported.path();if(!path)throw Error('Missing GeoJSON download');
  expect(JSON.parse(await readFile(path,'utf8'))).toEqual(fixture);
  await page.getByText('Connect QGIS or your field survey',{exact:true}).click();
  await page.getByRole('button',{name:'Clear imported survey',exact:true}).click();
  await expect(page.getByRole('heading',{name:'No survey imported'})).toBeVisible();
  await expect(page.getByRole('checkbox',{name:'Show synthetic demo scene (not real data)'})).not.toBeChecked();
  expect(external,'survey navigation should not contact a remote basemap or API').toEqual([]);
});
