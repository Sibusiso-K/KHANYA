"""Segmentation: backbone + decoder.

Assigns a mineral label per pixel from the reflectance and polarimetry stack.

Backbone is ``timm`` (Apache-2.0). DINOv3 is blocked — non-transferable, no patent grant
(gauntlet S3, SBOM.md). Splits are by locality, never by patch or image (CLAUDE.md Rule 2):
patch-level splits void conformal exchangeability and silently invalidate every downstream
metric.

The implemented, dependency-light guards are exposed by :mod:`reefprint.trust.split` and
:mod:`reefprint.trust.baseline`; the optional model backbone is declared in
:mod:`reefprint.segment.backbone`.
"""
