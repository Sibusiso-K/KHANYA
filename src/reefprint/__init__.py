"""REEFPRINT — a computational ore microscope.

Identifies opaque ore minerals and quantifies their deportment by multispectral quantitative
reflectance plus full linear Stokes polarimetry, with calibrated uncertainty and an explicit
refusal mechanism.

The physics, in one line: opaque minerals have no diagnostic molecular *vibrational* absorption
features, so they are identified by specular reflectance, bireflectance and anisotropy. Our
illumination is **unpolarised**, with the analyser the only polarising element (ADR-0005), so
the polarisation is generated on reflection: pentlandite is cubic and stays **flat** through a
full analyser rotation — DOLP 0, no modulation — while pyrrhotite is anisotropic and lights up.
That distinction governs PGE deportment. The classical *crossed-polars* observation is a
**stage** rotation and is a different instrument; see :mod:`reefprint.polarim.geometry`.

See ``CLAUDE.md`` for the rules that constrain every module here. Rule 1 — *never invent a
number* — is the one that applies to every subpackage without exception, so its guard lives
here at the top level rather than inside any one of them: :mod:`reefprint.quantity`. A
:class:`~reefprint.quantity.Quantity` cannot be constructed without saying where its number
came from, and the provenance travels through the arithmetic, weakest input winning.
"""

__version__ = "0.1.0"
