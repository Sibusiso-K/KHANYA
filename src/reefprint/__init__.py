"""REEFPRINT — a computational ore microscope.

Identifies opaque ore minerals and quantifies their deportment by multispectral quantitative
reflectance plus full linear Stokes polarimetry, with calibrated uncertainty and an explicit
refusal mechanism.

The physics, in one line: opaque minerals have no diagnostic molecular absorption features, so
they are identified by specular reflectance, bireflectance and anisotropy under crossed polars.
Pentlandite is cubic and stays dark through a full analyser rotation; pyrrhotite is anisotropic
and lights up. That distinction governs PGE deportment.

See ``CLAUDE.md`` for the rules that constrain every module here.
"""

__version__ = "0.1.0"
