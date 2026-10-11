# Spatial refinement handover

The spatial page now has working survey tools rather than three camera presets for the same scene.

## Implemented

- The default is an empty measured-survey workspace. Import a validated WGS84 Point GeoJSON containing collar elevation, `depth_m`, an ID and optional exact `sample_id`.
- The plan map provides a metre grid, scale bar, north indicator, coordinate query, pan, zoom, fit and centre-on-selection. It makes no remote requests. A matching sample ID opens the same sample used by the analysis workspace.
- The east–west section uses real supplied collar elevations and depth values. An adjustable north centre and corridor width filter which records are projected into the section; excluded records are marked in the record list.
- The 3D scene supports camera focus/reset, vertical exaggeration and record selection. In the opt-in synthetic scene, each authored lithological domain can be hidden and its opacity changed; the section slider cuts the block with a closing face.
- Survey search, original-coordinate GeoJSON export and clear/import actions are functional. Clearing a survey does not silently switch to synthetic geology.

## Evidence and tests

`node frontend/scripts/test-spatial-geometry.mjs` passes five tests covering map aspect, projection inversion, section corridor boundaries, single-point fitting and bounded zoom. Existing parser tests remain unchanged.

TypeScript compilation passed with `npx tsc --noEmit`.

The browser test `frontend/e2e/spatial-tools.spec.ts` passed the import → map coordinate query → zoom → linked record selection → corridor filter → original GeoJSON export → clear sequence. It asserts no remote assets or map APIs are requested. The existing mobile/offline browser test also passed. After reviewing the mobile screenshot, the SVG's left gutter was widened to avoid clipping full elevation labels; the root release run will verify that final cosmetic adjustment with the complete browser suite.

Browser screenshots use an explicitly labelled two-point test fixture, not a measured mining survey:

- `frontend/test-results-spatial-refinement/spatial-tools-survey-impor-4d659-without-fabricating-geology/survey-map-desktop-fixture.png`
- `frontend/test-results-spatial-refinement/spatial-tools-survey-impor-4d659-without-fabricating-geology/survey-section-desktop-fixture.png`
- `frontend/test-results-spatial-refinement/spatial-tools-survey-impor-4d659-without-fabricating-geology/survey-section-mobile-fixture.png`

## Scope and limitations

The map is an offline survey grid, not an online terrain basemap. The shared parser uses a local equirectangular approximation and restricts the import to a 25 km radius. Original WGS84 coordinates are preserved on export. Survey imports remain in per-account browser storage; they are not yet stored in Supabase.

The supplied collar/depth contract does not contain inclined downhole surveys, measured terrain meshes or lithological contacts. Real record traces are explicitly vertical approximations. No orebody, 3D mineral volume or lithology is inferred from a two-dimensional microscopy mask. Synthetic lithology is visibly labelled, opt-in and not linked to S2 images. This is a useful viewing workflow, not a claim to reproduce Leapfrog's modelling engine or all QGIS geoprocessing.

For a next implementation, add a rights-cleared measured terrain/mesh interchange and downhole-survey contract, then validate coordinate reference transformations and site geometry with a geologist before adding interpolation. Keep computer-vision phase evidence separate from geographic interpretation.

## Files

Owned spatial changes: `frontend/src/Spatial.tsx`, `frontend/src/spatial.css`, `frontend/src/SpatialViews.tsx`, `frontend/src/spatialGeometry.ts`, `frontend/scripts/test-spatial-geometry.mjs`, `frontend/e2e/spatial-tools.spec.ts`; two badge wording assertions updated in `frontend/e2e/mobile.spec.ts`.

No new packages, credentials, third-party map subscriptions, commits or server restarts were needed for these changes. Root integration still needs the final frontend build and release verification.
