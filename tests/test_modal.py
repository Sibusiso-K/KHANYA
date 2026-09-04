"""Liberation measurement, and the crash that reached it from the dashboard.

`liberation_index` distinguishes "no measurement" from "zero liberation". The
advisor branches on that distinction, so conflating them would turn a field
where the payload was never detected into a confident "grind finer".
"""
import numpy as np

from src import modal


def _solid_particle(size=40, payload_value=1):
    """One square particle of payload, comfortably above MIN_PARTICLE_PIXELS."""
    labels = np.zeros((size, size), dtype=np.int32)
    labels[10:30, 10:30] = payload_value
    payload_mask = labels == payload_value
    return labels, payload_mask


class TestLiberationIndex:
    def test_no_payload_returns_none_not_zero(self):
        """'We did not measure it' and 'it is zero' are different claims.

        Returning 0.0 here would read downstream as fully-locked ore and earn a
        confident 'grind finer' on a field where the payload was simply absent.
        """
        labels = np.zeros((20, 20), dtype=np.int32)
        labels[5:15, 5:15] = 2  # gangue only, no payload phase
        liberation, _ = modal.liberation_index(labels, payload_mask=labels == 1)
        assert liberation is None

    def test_a_fully_liberated_particle_scores_one(self):
        labels, payload = _solid_particle()
        liberation, n_particles = modal.liberation_index(labels, payload)
        assert liberation == 1.0
        assert n_particles == 1

    def test_liberation_is_bounded_to_the_unit_interval(self):
        labels, payload = _solid_particle()
        liberation, _ = modal.liberation_index(labels, payload)
        assert 0.0 <= liberation <= 1.0

    def test_payload_locked_in_gangue_scores_below_a_liberated_grain(self):
        """A payload core wrapped in gangue is one poorly-liberated particle."""
        locked = np.full((40, 40), 2, dtype=np.int32)  # gangue everywhere
        locked[0:5, 0:5] = 0                            # a little resin
        locked[18:22, 18:22] = 1                        # small payload core
        locked_liberation, _ = modal.liberation_index(locked, locked == 1)

        free_labels, free_payload = _solid_particle()
        free_liberation, _ = modal.liberation_index(free_labels, free_payload)

        assert locked_liberation < free_liberation

    def test_sparse_payload_that_opens_away_does_not_crash(self):
        """Regression, entry (23).

        Refinement opens the mask morphologically. Scattered single payload
        pixels survive the payload test but are erased by the opening, leaving
        a zero-size reduction. This crashed - and it was reachable from the
        dashboard on any sparse upload, not just from the analysis script.
        """
        labels = np.zeros((60, 60), dtype=np.int32)
        labels[10:50, 10:50] = 2                     # a gangue body
        labels[15, 15] = labels[25, 25] = labels[35, 35] = 1  # isolated pixels

        liberation, n_particles = modal.liberation_index(
            labels, payload_mask=labels == 1, refine=True
        )

        # The contract is "returns, with liberation possibly None" - never raises.
        assert liberation is None or 0.0 <= liberation <= 1.0
        assert n_particles >= 0

    def test_an_all_background_field_does_not_crash(self):
        """The other end of the same class of bug: nothing in the field at all."""
        empty = np.zeros((30, 30), dtype=np.int32)
        liberation, n_particles = modal.liberation_index(empty, empty == 1)
        assert liberation is None
        assert n_particles == 0
