# ADR-0001 — OME-TIFF via `tifffile`, not Bio-Formats

- **Date:** 2026-08-15
- **Status:** Accepted
- **Decider:** *(unassigned — CLAUDE.md open question 4)*
- **Relates to:** gauntlet **S3** (licence stack unassignable) · CLAUDE.md Rule 7 · `SBOM.md`

## Context

CLAUDE.md's stack line lists "OME-TIFF via Bio-Formats" as the image container. OME-TIFF is the
right container — it carries acquisition metadata in the file rather than in a sidecar someone
loses, which is what Rule 1 needs from a provenance chain.

Bio-Formats is the wrong *route to it here*. The OME Bio-Formats distribution is GPL-2.0. Linking
GPL-2.0 into a deliverable that must be assignable to Mintek is precisely the failure mode S3
identified and that the DINOv3 removal was meant to close. Solving it for the model backbone and
then reintroducing it at the I/O layer would leave the licence argument no better than v1's.

It is also a JVM dependency inside an otherwise pure-Python stack that has to run offline on one
laptop (week-5 gate) and on a Pi.

## Decision

Use `tifffile` (BSD-3-Clause) for all OME-TIFF reading, writing and OME-XML metadata.

## Consequences

- The licence stack stays permissive end-to-end and the SBOM claim survives inspection.
- No JVM. One less thing that can fail on stage.
- Proprietary vendor microscope formats (`.czi`, `.nd2`, `.lif`) are no longer readable in-process.
  If one is ever needed, Bio-Formats is used **offline as a manual conversion tool** to produce an
  OME-TIFF, and never appears as a dependency of shipped code.
- `tifffile`'s OME-XML support is good but not exhaustive. Anything it cannot express goes in a
  documented custom namespace, not silently dropped.

## Alternatives rejected

| Option | Why not |
|---|---|
| Bio-Formats (`python-bioformats` / `scyjava`) | GPL-2.0. Unassignable. JVM. Gauntlet S3. |
| Plain TIFF + JSON sidecar | Metadata separates from pixels the first time a file is copied. Rule 1 needs provenance attached to the data. |
| HDF5 / Zarr | Good containers, but not what the microscopy world reads, and OME-TIFF is what makes the open benchmark usable by someone else. |

## What would change this

`tifffile` proving unable to round-trip the OME-XML fields the acquisition metadata needs — in
which case the answer is a documented extension namespace, not Bio-Formats. Or Mintek stating in
writing that a GPL-2.0 component is acceptable in the assigned deliverable.
