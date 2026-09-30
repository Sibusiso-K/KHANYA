---
name: REEFPRINT / KHANYA workbench
description: A white instrument workbench for mineral images, evidence and explicitly simulated decisions.
colors:
  blue: "#22578d"
  blue-light: "#edf3fa"
  blue-hover: "#18466f"
  ink: "#1b2d40"
  muted: "#536779"
  line: "#dbe3e9"
  surface: "#fff"
  canvas: "#f1f4f6"
  active-nav-copper: "#c27543"
  active-nav-text: "#1f476b"
  focus: "#2e70df"
  phase-chalcopyrite: "#f28136"
  phase-pyrrhotite: "#119eae"
  phase-pentlandite: "#9562d1"
  phase-magnetite: "#d6ac25"
  phase-background: "#8c96a1"
  domain-weathered-cover: "#a1b4a1"
  domain-upper-host: "#c0b699"
  domain-marker-horizon: "#748d9b"
  domain-lower-host: "#b7a2bc"
  domain-basement: "#536b7e"
typography:
  headline:
    fontFamily: '"Public Sans Variable", "Segoe UI", sans-serif'
    fontSize: "27px"
    fontWeight: 650
    lineHeight: 1.4
    letterSpacing: "-0.85px"
  title:
    fontFamily: '"Public Sans Variable", "Segoe UI", sans-serif'
    fontSize: "15px"
    fontWeight: 650
    lineHeight: 1.5
    letterSpacing: "-0.2px"
  body:
    fontFamily: '"Public Sans Variable", "Segoe UI", sans-serif'
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.65
  button:
    fontFamily: '"Public Sans Variable", "Segoe UI", sans-serif'
    fontSize: "12px"
    fontWeight: 550
rounded:
  badge: "4px"
  field: "5px"
  button: "6px"
  panel: "8px"
  spatial-workbench: "10px"
spacing:
  button-gap: "8px"
  workbench-gap: "14px"
  section-head: "17px 18px 14px"
  button-padding: "9px 13px"
components:
  button-primary:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.surface}"
    typography: "{typography.button}"
    rounded: "{rounded.button}"
    padding: "{spacing.button-padding}"
  button-primary-hover:
    backgroundColor: "{colors.blue-hover}"
  panel:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.panel}"
  spatial-workbench:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.spatial-workbench}"
---

# Design System: REEFPRINT

## Overview

The approved direction is a white three-panel workbench. Restrained blue actions, copper active navigation and locally bundled Public Sans Variable refine that direction. This is an extraction of the implemented interface, not a proposal for a new identity; no additional creative metaphor has been approved.

The interface serves mineral researchers inspecting reflected-light micrographs, recorded evaluation evidence and a local process simulator. Actual specimen images, checkpoint identity and source labels anchor the visual presentation. Dense supporting controls surround the image or spatial canvas, while evidence remains readable in dedicated views.

Key characteristics:

- White, bordered instrument panels on a cool grey page.
- Compact typography with tabular numerals and explicit provenance.
- Separate mineral-phase, geological-domain and interaction colours.
- Dedicated Phase identification, Accuracy and Process simulator workflows.

## Colors

The frontmatter contains the effective shared palette after the refinement overrides in `frontend/src/styles.css`; source CSS remains authoritative. Blue is the primary action colour. Copper is a navigation state indicator, not a mineral class or a warning threshold. White surfaces, ink text, muted secondary text and fine grey borders establish hierarchy.

Mineral colours are fixed by `palette` in `App.tsx`: chalcopyrite, pyrrhotite, pentlandite, magnetite and background. Reuse those mappings in image legends, composition bars and report rows. Do not recolour classes to match the interface accent. The fallback to an API-provided colour is retained for unknown classes.

The muted geological domain palette follows `rockNames` and `rockColors` in `Spatial.tsx`, in the order captured by the frontmatter. It describes synthetic rock units only. Preserve the visible statement that these colours are not predicted mineral phases. Spatial selection uses separate warm marker colours in the implementation; it does not imply mineral composition.

## Typography

Public Sans Variable is bundled through `@fontsource-variable/public-sans`, with Segoe UI and sans-serif fallbacks. The root is 14px/400, with optical sizing enabled, synthetic font styles disabled and tabular numerals. Paragraphs use the body role; dense provenance and legends commonly use 11px. This is a compact research UI, not a marketing display scale.

Workspace headings use the headline role, reducing to 25px at 1000px and 22px at 700px. Section headings use the title role. H3 defaults to 13px/650 with a 1.5 line height. Phase values use 17px in the final refinement; recorded metric values use 30px/650. Values and confidence must come from the actual application data, never illustrative typography samples presented as results.

## Layout

The main container is capped at 1780px and centred, with desktop padding of 25px 26px 0. The mineral workbench uses `230px minmax(380px,1fr) 290px` and a 14px gap. The geological workbench uses `210px minmax(300px,1fr) 260px`, a 640px minimum height and shared panel borders. Its layers and record list sit left, canvas in the centre and inspector right.

At 1250px and below, mineral columns become `190px minmax(300px,1fr) 250px` with a 10px gap; geological columns become `180px minmax(280px,1fr) 225px`. At 1000px, navigation wraps beneath the masthead and both workbenches use two columns; the phase panel or spatial inspector spans the row below. Main padding becomes 20px 16px 0. At 700px, panels stack and main padding becomes 17px 12px 0. The sample library uses its mobile toggle, the spatial point list scrolls horizontally, and inspector content follows the canvas. Mobile navigation stacks each icon over its label.

The spatial renderer has minimum heights of 470px on desktop, 450px at 1250px, 490px at 1000px and 390px at 700px. At 1600px and above the mineral image stage increases to 455px and its sample list to 550px. These are observed breakpoints, not a universal spacing scale.

Print rules remove navigation and controls. The spatial scene has print sizing, but source inspection alone does not verify WebGL canvas capture in every browser.

## Elevation & Depth

The interface is flat by default: borders, white surfaces and subtle tonal fills carry structure. Selected segmented controls use `0 1px 3px #17304e0a`; the spatial mode badge uses `0 2px 6px #152a3610`. Do not add broad decorative card shadows. The rendered geological scene has lighting and material depth, distinct from UI elevation.

## Shapes

Small corner radii distinguish controls and surfaces: badges 4px, fields and segmented groups 5px, buttons 6px, ordinary panels 8px, and the combined geological workbench 10px. The source still declares `--radius:9px`, but the final `.panel` rule overrides it to 8px; the frontmatter records the effective panel value. Circles are reserved for dots, point markers and workflow step numbers. Borders are normally 1px; active top navigation uses a 3px bottom border.

## Components

Buttons are compact and explicit. Primary buttons use blue, white text, 9px 13px padding and a 38px minimum height. Hover uses the darker blue. Disabled controls retain their layout, show reduced opacity and a not-allowed cursor. At 700px, generic button and icon controls receive a 40px minimum height; specialised selectors retain their own more specific sizes. Do not claim that every touch target reaches 44px.

Focus-visible controls use a 3px blue outline with a 3px offset. Search uses a 2px blue focus-within outline. Search and record fields retain descriptive labels. The app provides a skip link and a keyboard-selectable spatial record list alongside canvas interaction.

Navigation keeps the copper active underline and dark blue active text. Segmented controls use a white selected segment on a pale grey tray. Selection must also remain available through text, borders or control state, not colour alone.

The image viewer distinguishes Original acquisition, Prediction over original and Model prediction, with Fresh inference or Saved inference provenance. Composition is predicted image-area fraction. Confidence is an uncalibrated model score; it is not accuracy. Accuracy belongs to the checkpoint-specific recorded evaluation, with its source and limitations.

The geological workbench explicitly separates Geology demo from My survey. Demo layers and drillholes are procedural, synthetic and unlinked to S2 images. Imported GeoJSON supplies coordinates; unavailable terrain and geological layer controls are disabled. Collar-to-sample traces are vertical approximations. Section mode projects all points east-west, rather than claiming a thin section slice. Retain the import constraints and local-storage disclosure shown by the app.

The process view is labelled as a demonstration using a local simulator. A simulation is an explicit action; low-confidence or unverified inputs hold the existing setting. Exported decision evidence must carry the actual model result, report reference and simulator response. No recovery gain or live plant control is implied.

Implementation limits: this documentation was verified against source, not computed browser styles or a full accessibility audit. The stylesheets contain historical declarations followed by refinement overrides; resolve the cascade before extending components. The 3D canvas requires WebGL, while the record list supplies keyboard selection. Deployment, backend availability and model execution are outside this design extraction.

## Do's and Don'ts

- Do preserve the approved white workbench and use blue for actions, copper for active navigation.
- Do preserve phase and domain colour mappings independently.
- Do keep source, checkpoint, synthetic-demo and simulator labels visible with their content.
- Do use real imagery, returned results and recorded evidence; show empty or unavailable states when data is missing.
- Do retain reduced-motion support: the source removes transitions and reduces animation durations when requested.
- Don't infer assays, depth, grade, orebody geometry or recovery gains from an image.
- Don't imply a demo point locates the current analysis sample.
- Don't treat field photographs as the trained reflected-light modality.
- Don't claim cloud sync for records that are saved on-device.
