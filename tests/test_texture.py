"""Data-independent texture mechanics; the real-data falsification remains a domain gate."""

from __future__ import annotations

import numpy as np
import pytest

from reefprint.texture.grains import association_matrix, extract_grains


def test_grains_are_extracted_from_a_labelled_map():
    """The unit of analysis is the grain, not the specimen. Gauntlet F3."""
    labels = np.array([[1, 1, 0, 2], [1, 0, 0, 2], [0, 3, 3, 2]])
    grains = extract_grains(labels, phase_names={1: "chromite", 2: "pentlandite", 3: "gangue"})
    assert len(grains) == 3
    assert {grain.mineral for grain in grains} == {"chromite", "pentlandite", "gangue"}
    assert sum(grain.area_px for grain in grains) == 8


def test_association_matrix_is_symmetric_and_normalised():
    """Mineral-mineral contact statistics. A shared boundary is shared in both directions."""
    names, matrix = association_matrix(np.array([[1, 1, 2], [1, 2, 2]]))
    assert names == ("label-1", "label-2")
    assert matrix == pytest.approx(matrix.T)
    assert matrix.sum() == pytest.approx(1.0)


def test_three_phase_contacts_preserve_symmetry_with_unequal_boundaries():
    # Two 1-2 edges and one 2-3 edge; each appears in both directions.
    _, matrix = association_matrix(np.array([[1, 2, 1, 0, 2, 3]]))
    expected = np.array([[0, 2, 0], [2, 0, 1], [0, 1, 0]]) / 6
    assert matrix == pytest.approx(expected)
    assert matrix == pytest.approx(matrix.T)


@pytest.mark.placeholder
def test_falsification_test_controls_for_cr2o3_and_pyroxene_fraction():
    """**Week-2 gate. H0: after controlling for Cr2O3 and pyroxene fraction, texture carries no
    additional predictive signal.**

    Nested model comparison, grouped by locality, CI at honest n. Rule 9: this is a deliverable,
    not a risk — the result is reported either way, and if H0 survives we say so publicly and
    pivot to the oxidation index.
    """
    pytest.fail(
        "NOT BUILT — texture: real texture-plus-chemistry dataset remains the Week-2 domain-lead block"
    )
