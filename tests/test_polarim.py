"""Placeholder — reefprint.polarim. Week-1 gate, output half. The load-bearing module.

These are physics invariants, so when they are built they become hypothesis property tests,
not example tests. An invariant that only holds for the three arrays you happened to try is
not an invariant.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.placeholder


def test_stokes_recovery_inverts_malus_law():
    """I(theta) = S0/2 + (S1 cos 2theta + S2 sin 2theta) / 2.

    Synthesise a series from known (S0, S1, S2), recover it, and require round-trip equality.
    """
    pytest.fail("NOT BUILT — polarim: linear Stokes recovery from a rotation series")


def test_recovered_stokes_vector_is_physically_realisable():
    """S0**2 >= S1**2 + S2**2, everywhere, for any input.

    Violation means the fit is unconstrained, not that the specimen is exotic.
    """
    pytest.fail("NOT BUILT — polarim: realisability constraint")


def test_degree_of_linear_polarisation_is_bounded():
    """DOLP = sqrt(S1**2 + S2**2) / S0 lies in [0, 1]."""
    pytest.fail("NOT BUILT — polarim: DOLP")


def test_specimen_rotation_rotates_stokes_by_twice_the_angle():
    """Rotating the specimen by phi rotates (S1, S2) by 2 phi and leaves S0 and DOLP fixed.

    This is the test that catches an angle convention error, which is the single most likely
    way to get a plausible-looking anisotropy map that means nothing.
    """
    pytest.fail("NOT BUILT — polarim: rotation covariance")


def test_isotropic_phase_stays_dark_through_full_rotation():
    """**This is the week-1 gate.**

    Pentlandite is cubic: anisotropy near zero through a full analyser rotation. Pyrrhotite has
    moderate bireflectance: it lights up. Pass means those two separate on the anisotropy map.
    """
    pytest.fail("NOT BUILT — polarim: anisotropy map, week-1 gate")
