import {test, expect, type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

// Controlled API fixtures verify browser behavior, not live inference,
// authentication, or a fresh evaluation. Scores come from frozen repo evidence.
const metricsBytes = readFileSync(new URL('../../reports/native-selected-test-20261001/native_selected_test_metrics.json', import.meta.url));
const recordedMetricsSha = '13bed0c61569fb840bdbb4039df8264655c14f3652d7ceb38dde8ed483c05692';
const measured = JSON.parse(metricsBytes.toString('utf8'));
const checkpoints = JSON.parse(readFileSync(new URL('../../reports/checkpoint-metrics.json', import.meta.url), 'utf8'));
const activeSha = checkpoints.approved_for_demo;
const activeCheckpoint = checkpoints.checkpoints[activeSha];
const activeReport = {
  model_sha: activeSha, checkpoint_available: true, model_approved: true,
  approved_model_sha: activeSha, approved_reason: checkpoints.approved_reason,
  checkpoint_matches_report: true, report_source: activeCheckpoint.source,
  metrics: activeCheckpoint, limitations: ['Magnetite IoU is zero for the active checkpoint.'],
  download_url: '/api/report/download',
};
const colors = ['#8c96a1', '#f28136', '#d6ac25', '#119eae', '#9562d1'];
const candidateEvidence = {
  evaluation_id: measured.evaluation_id, model_sha: measured.checkpoint_sha256,
  active_model_sha: activeSha, candidate_is_active: false, verified_evidence: true,
  protocol_sha: measured.protocol_sha256, completed_at: measured.finished_at_utc,
  candidate_epoch: measured.candidate_epoch, method: measured.method,
  selection_rule: measured.selection_rule,
  metrics: {
    mean_iou: measured.mean_iou, foreground_macro_iou: measured.foreground_macro_iou,
    pixel_accuracy: measured.pixel_accuracy, n_test_sections: measured.n_test_sections,
    classes: measured.class_names.map((name:string, index:number) => ({
      name, color: colors[index], iou: measured.iou_per_class[index],
      recall: measured.recall_per_class[index], precision: measured.precision_per_class[index],
      support_pixels: measured.ground_truth_pixels_per_class[index],
      false_positive_pixels: measured.fp_per_class[index],
    })),
  },
  limitations: [
    measured.historical_test_caveat,
    'Evaluation does not approve or deploy this checkpoint. Active inference, assistant scores and simulator gates remain separate.',
  ],
  downloads: [{
    key: 'metrics', filename: 'native_selected_test_metrics.json',
    sha256: recordedMetricsSha,
    url: '/api/reports/native-candidate/download/metrics',
  }],
};

type CandidateState = 'ready' | 'unavailable' | 'malformed';
async function mockReports(page:Page, state:() => CandidateState = () => 'ready') {
  const calls:{path:string; method:string}[] = [];
  await page.route('**/api/**', async route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    calls.push({path, method: request.method()});
    if (path === '/api/reports/native-candidate') {
      if (state() === 'unavailable') {
        await route.fulfill({status: 503, json: {detail: 'Candidate evidence is unavailable in this fixture.'}});
      } else if (state() === 'malformed') {
        await route.fulfill({json: {verified_evidence: true, metrics: {classes: []}}});
      } else {
        await route.fulfill({json: candidateEvidence});
      }
      return;
    }
    if (path === '/api/reports/native-candidate/download/metrics') {
      await route.fulfill({
        status: 200, body: metricsBytes,
        headers: {'content-type': 'application/json', 'content-disposition': 'attachment; filename="REEFPRINT-native_selected_test_metrics.json"'},
      });
      return;
    }
    let body:unknown = {};
    if (path === '/api/config') body = {auth_required: false, cloud_sync: false};
    else if (path === '/api/samples') body = [{id: 'test_11', thumbnail_url: '', dimensions: [512, 512], dataset: 'Controlled S2 fixture', has_prediction: false}];
    else if (path === '/api/report') body = activeReport;
    else if (path === '/api/health') body = {status: 'ok', checkpoint_available: true, model_sha: activeSha, model_approved: true, approved_model_sha: activeSha};
    else if (path === '/api/samples/test_11/record') body = {sample_id: 'test_11', version: 0, updated_at: null, record: {}};
    else if (path === '/api/samples/test_11') body = {id: 'test_11', result_id: null, raw_url: '', phases: [], verified: true};
    await route.fulfill({json: body});
  });
  await page.goto('/');
  await expect(page.getByRole('heading', {name: 'From specimen to insight'})).toBeVisible();
  await page.getByRole('navigation', {name: 'Main navigation'}).getByRole('button', {name: 'Reports', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Evidence you can inspect'})).toBeVisible();
  return calls;
}

test('candidate evidence stays distinct from active scores, downloads explicitly, and fits a 375px page', async ({page}) => {
  await page.setViewportSize({width: 375, height: 812});
  await mockReports(page);
  const candidate = page.getByRole('region', {name: /Retrained candidate.*measured test evidence/});
  const activeEvidence = page.locator('.evidence-panel');
  await expect(candidate.getByText('Candidate not deployed', {exact: true})).toBeVisible();
  await expect(activeEvidence.getByText(activeCheckpoint.mean_iou.toFixed(3), {exact: true})).toBeVisible();
  await expect(activeEvidence.getByText(measured.mean_iou.toFixed(3), {exact: true})).toHaveCount(0);
  await expect(candidate.getByText(measured.mean_iou.toFixed(3), {exact: true})).toBeVisible();
  await expect(candidate.getByText(/precision is only 25.5%/)).toBeVisible();
  await expect(candidate.getByText(/Most predicted magnetite pixels are incorrect/)).toBeVisible();
  await expect(candidate.getByText(/This is a fixed regression check, not new blind field validation/)).toBeVisible();

  await candidate.getByText('Protocol, checkpoint identity and limitations', {exact: true}).click();
  await expect(candidate.getByText(measured.checkpoint_sha256, {exact: true})).toBeVisible();
  await expect(candidate.getByText(activeSha, {exact: true})).toBeVisible();

  const downloadPath = '/api/reports/native-candidate/download/metrics';
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    candidate.getByRole('button', {name: 'Full evidence JSON', exact: true}).click(),
  ]);
  // Native anchor downloads can bypass page request events. Verify the browser's
  // actual download URL and completed file bytes instead of waiting for fetch.
  expect(new URL(download.url()).pathname).toBe(downloadPath);
  expect(download.suggestedFilename()).toBe('REEFPRINT-native_selected_test_metrics.json');
  expect(await download.failure()).toBeNull();
  const savedPath = await download.path();
  expect(savedPath, 'Chromium must provide a completed file').not.toBeNull();
  const downloadedBytes = readFileSync(savedPath!);
  expect(createHash('sha256').update(downloadedBytes).digest('hex')).toBe(recordedMetricsSha);
  await expect(candidate.getByRole('status')).toHaveText('Download requested: native_selected_test_metrics.json.');

  // The phase table may scroll inside its container; the page must not widen.
  const table = candidate.locator('.table-scroll');
  expect(await table.evaluate(element => {
    const view = element as HTMLElement;
    return view.scrollWidth > view.clientWidth && ['auto', 'scroll'].includes(getComputedStyle(view).overflowX);
  })).toBe(true);
  await table.evaluate(element => {element.scrollLeft = element.scrollWidth;});
  expect(await table.evaluate(element => element.scrollLeft > 0)).toBe(true);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await expect(activeEvidence.getByText(activeCheckpoint.mean_iou.toFixed(3), {exact: true})).toBeVisible();
});

test('unavailable and malformed candidate responses show unknown status and recover on retry', async ({page}) => {
  let state:CandidateState = 'unavailable';
  const calls = await mockReports(page, () => state);
  const candidate = page.getByRole('region', {name: /Retrained candidate.*measured test evidence/});
  await expect(candidate.getByText('Status unavailable', {exact: true})).toBeVisible();
  await expect(candidate.getByRole('alert')).toHaveText('Candidate evidence is unavailable in this fixture.');
  await expect(candidate.getByText('Candidate not deployed', {exact: true})).toHaveCount(0);

  state = 'malformed';
  await candidate.getByRole('button', {name: 'Retry evidence', exact: true}).click();
  await expect(candidate.getByRole('alert')).toContainText('The service did not return verified candidate evidence.');
  await expect(candidate.getByText('Status unavailable', {exact: true})).toBeVisible();
  await expect(candidate.getByText('Candidate not deployed', {exact: true})).toHaveCount(0);

  state = 'ready';
  await candidate.getByRole('button', {name: 'Retry evidence', exact: true}).click();
  await expect(candidate.getByText('Candidate not deployed', {exact: true})).toBeVisible();
  await expect(candidate.getByText(measured.mean_iou.toFixed(3), {exact: true})).toBeVisible();
  await expect(candidate.getByText('Status unavailable', {exact: true})).toHaveCount(0);
  await expect(candidate.getByRole('alert')).toHaveCount(0);
  expect(calls.filter(call => call.path === '/api/reports/native-candidate' && call.method === 'GET').length).toBeGreaterThanOrEqual(3);
});

