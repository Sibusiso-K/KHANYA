"""Polarimetry: linear Stokes parameters, bireflectance, anisotropy.

Owns the week-1 gate's output half. Given a rotation series I(theta), recovers per-pixel
S0, S1, S2, degree of linear polarisation and an anisotropy map.

This is the module the whole project stands on. Published automated optical mineralogy uses
non-polarised light; adding full Stokes polarimetry to quantitative reflectance is the claim.

Physics invariants that must hold, and are property-tested rather than assumed:

- Malus's law: I(theta) = S0/2 + (S1 cos 2theta + S2 sin 2theta) / 2
- Physical realisability: S0**2 >= S1**2 + S2**2
- DOLP = sqrt(S1**2 + S2**2) / S0 lies in [0, 1]
- Rotating the specimen rotates (S1, S2) by 2x the angle and leaves S0 and DOLP unchanged

Which element rotated is not knowable from the frames' filenames, and getting it wrong is
silent — see :mod:`reefprint.polarim.geometry`, which decides it from the harmonic content
instead. Finding N3.
"""
