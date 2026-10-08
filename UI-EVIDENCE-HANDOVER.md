# White workbench UI and grain evidence handover

Implemented in the existing live MVP worktree. No commits or pushes made.

## Changes

- Dedicated Dashboard navigation with Overview.tsx. Counts use returned samples; health supplies status; the report supplies recorded metrics and provenance; the selected specimen uses its actual result. Missing data stays unavailable. Workspace remains the initial page.
- Lazy GrainExplorer.tsx below the preserved three-panel workspace. It fetches the grain report and lossless grain-ids PNG for the exact current result ID; no grains are reconstructed or invented.
- Full 24-bit RGB grain IDs map resized canvas clicks to exact source pixels. Selected grain pixels are highlighted. The table supports keyboard selection, phase filtering and pagination.
- Details show returned pixel area, equivalent diameter, within-grain phase composition and the backend's 2D liberation flag. Expandable tables expose boundary association and size-bin liberation. No micron scale is assumed.
- Grain exports carry the actual result properties, stored evidence and a scope disclosure, preserving source/model/result provenance.
- App and Dashboard images use the parent's authenticated AuthImage client. Grain canvas images use authenticatedMedia and released temporary URLs. Removed the local api helper in favour of the shared client.
- White panels, Public Sans, blue actions, copper navigation and fixed phase colours retained. Mobile app text has a 12px minimum, controls wrap, tables scroll within the panel. Grain canvas preserves aspect ratio and caps its displayed height at 520px.
- Null confidence displays Unavailable. Magnetite missed note depends on actual recorded magnetite IoU. Report section count comes from the recorded metrics.

## Owned files

App.tsx and styles.css; new Overview.tsx, GrainExplorer.tsx, grainPixels.mjs and grainPixels.d.mts; scripts/test-grain-pixels.mjs; e2e/grains.spec.ts; e2e/mobile.spec.ts (Dashboard added); playwright.config.ts (optional REEFPRINT_BROWSER_CHANNEL).

Parent subsequently owns App auth/download/deployment copy integration and can append auth styles. The shared authenticated client and main entry point belong to the parent.

## Verification

- Production npm build passed. Main and Spatial retain Vite's existing >500KB chunk advisory. GrainExplorer is a separate lazy chunk.
- Final `node node_modules/typescript/bin/tsc --noEmit` passed after all grain sizing and export changes.
- `node --test scripts/test-grain-pixels.mjs`: 2 passed, covering RGB IDs through 0xFFFFFF and resized pointer boundaries.
- `$env:REEFPRINT_BROWSER_CHANNEL='chrome'; npm run test:e2e -- --workers=1 --timeout=90000`: 2 passed. Grain checks cover exact decoded image selection, keyboard table selection, filtering, downloaded result/model provenance, and viewport overflow at 375px/1440px. Mobile checks cover Dashboard, Samples, Spatial, Process and Reports with all visible text >=12px.
- Default Playwright downloaded Chromium is absent. Concurrent installed-Chrome startup initially stalled; serial installed-Chrome checks passed. Optional channel uses installed Chrome/Edge without downloading a browser.
- Mobile and desktop screenshots under frontend/test-results/grains-grain-selections-fo-87fb0-able-with-result-provenance/ were visually inspected. They use explicit test fixtures, not live checkpoint measurements.
- Browser tests validate frontend interaction. Real model, backend and authenticated isolation need the parent's/backend agent's separate verification.
- Final offline-runtime browser assertions passed in both tests with auth_required:false: no HTTP(S) requests outside the local base origin were observed across page navigation, image/grain loading and exports. Data/blob URLs are excluded. The final serial Chrome run completed with 2 passed in 20.2 seconds.

Keep shared-client authenticated download handlers for protected report/decision files. No cloud sync or operational plant outcome is inferred by the new UI.
