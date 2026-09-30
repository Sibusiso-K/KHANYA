import {test, expect} from '@playwright/test';

test('all workbench pages remain legible and unclipped at 375px', async ({page}) => {
  const externalRequests:string[]=[];
  const localOrigin=new URL(test.info().project.use.baseURL as string).origin;
  page.on('request',request=>{const url=new URL(request.url());if(['http:','https:'].includes(url.protocol)&&url.origin!==localOrigin)externalRequests.push(request.url())});
  await page.route('**/api/**', async route => {
    const url = route.request().url();
    let body: unknown = {};
    if (url.endsWith('/api/config')) body = {auth_required:false,cloud_sync:false};
    if (url.endsWith('/api/samples')) body = [{id:'test_11',thumbnail_url:'data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=',dimensions:[512,512],dataset:'Held-out S2',has_prediction:false}];
    if (url.endsWith('/api/report')) body = {model_sha:'abc',checkpoint_available:false,checkpoint_matches_report:false,report_source:'test',metrics:null,limitations:[],download_url:''};
    if (url.endsWith('/api/health')) body = {status:'ok',checkpoint_available:false};
    if (url.endsWith('/api/samples/test_11/record')) body = {sample_id:'test_11',version:0,updated_at:null,record:{}};
    if (url.endsWith('/api/samples/test_11')) body = {id:'test_11',result_id:null,raw_url:'',phases:[],verified:true};
    await route.fulfill({json:body});
  });
  await page.goto('/');
  await expect(page.getByRole('heading', {name:'From specimen to insight'})).toBeVisible();
  const pages = ['Dashboard','Samples','Spatial','Process','Reports'];
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
  expect(externalRequests,'local offline runtime must not request remote assets, APIs or auth services').toEqual([]);
});
