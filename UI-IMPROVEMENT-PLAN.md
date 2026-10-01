# UI improvement plan / implemented 1 October 2026

The approved white three-panel research workbench remains the default. This bounded pass adds useful operating preferences and clarifies real service state without altering model predictions, measured accuracy, source provenance or simulator approval gates.

| Before | After | Why |
| --- | --- | --- |
| One fixed white interface | White workbench plus Mineral night and Field paper | Researchers can choose low-light inspection or warm reading surfaces while retaining the approved default. |
| No account-scoped appearance | Browser preference namespaced to signed-in account, local workspace or signed-out login | One user does not inherit another user's chosen appearance; this is a preference, not cloud-synced project data. |
| Hardcoded white panels and dark captions | Theme tokens cover panels, controls, text, states, tables, evidence and the assistant | Changing only the page background leaves inaccessible mixed-theme surfaces. Mineral colours and image pixels stay unchanged. |
| No consolidated model/setup view | Settings shows the actual server SHA, CPU execution, approval, storage and read-only provider readiness | Users can distinguish deployed analysis from Kaggle experiments and optional language explanations. |
| API-key setup could be mistaken for a frontend action | Server-only ignored `.workbench/cloud.env` instructions, one provider at a time | Keys must not enter the browser, repository, sample notes or chat. Configuration is not proof of an API connection. |
| Minimal login and generic connecting state | Branded stacked-layer mark, clearer sign-in/create-account actions, separate confirmation notice and error, short mount transition | The opening flow communicates actual state without artificial delay or a fake analysis animation. |
| Signup displayed “Signing in” and confirmation as an error | Operation-specific button wording and a polite email-confirmation notice | Users understand what happened and what to do next. |
| Add micrograph / Full report | Upload micrograph (accessible label: Upload microscopy image) / Open accuracy report | Buttons name their action and destination. Existing analysis/simulation controls retain their actual meaning. |
| Local-server wording even on cloud record imports | Connected-backend wording | Reflects the deployed private Supabase workflow without claiming every browser preference is cloud saved. |

## Appearance and motion

- White: locally bundled Public Sans, blue action colour, copper navigation indicator.
- Mineral night: deep slate surfaces, light instrument text, cool blue actions and warm focus indication. No mask recolouring.
- Field paper: warm paper surfaces, forest actions, Georgia section headings and Public Sans body text. No font CDN or paid dependency.
- Motion is a one-time 220–420 ms brand/login mount transition tied to actual rendering. `prefers-reduced-motion` removes it. There is no added waiting timer, fake progress, scanner beam or altered tile telemetry.
- Appearance selection uses labelled native radio controls. Keyboard focus stays visible; mobile navigation scrolls rather than compressing seven page labels.

## Scientific input boundaries

The trained modality is prepared reflected-light microscopy resembling LumenStone S2. Upload checks accept PNG/JPEG/TIFF, maximum 25 MB, at least 512 pixels per side and at most 30 million pixels. The server also checks colour range. TIFF support does not make arbitrary TIFF acquisitions validated.

A phone photograph of an ore sample may pass file checks and produce a prediction, but it is outside the measured training/evaluation domain. Its output is not confirmed mineralogy, grade, abundance by volume or recovery. Use phone photos and voice notes as sample context. Extending phase identification to field or conveyor cameras requires expert labelled data and a separate evaluation.

## Verification and remaining work

Focused browser checks cover account-key isolation, persistence, invalid preference fallback, unchanged phase colours, mobile overflow, text contrast, keyboard radio selection, reduced motion and read-only provider setup. Root owns the production build, actual authenticated service restart, live screenshots and final repository publication.

Remaining: verify all pages with each theme on the actual authenticated build; prove the chosen provider with an explicitly consented real request after private server setup; connect surveyed spatial metadata if available; validate further specimen localities before field accuracy claims. Candidate weights remain separate from the active checkpoint until deployment is explicitly reviewed. Voice recognition quality, real plant control and recovery gains are not established by UI polish.
