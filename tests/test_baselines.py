"""Pure-function pieces of the trivial baselines, tested without touching the
real LumenStone archive - same reason test_bridge.py's archive-indexing tests
use a miniature synthetic namelist instead of the real dataset.
"""
import numpy as np

from src.segmentation.baselines import colour_only_predict


class TestColourOnlyPredict:
    def test_a_pixel_is_assigned_to_its_nearest_centroid(self):
        # Three well-separated classes in colour space: black, red, white.
        centroids = np.array([[0.0, 0.0, 0.0], [200.0, 0.0, 0.0], [255.0, 255.0, 255.0]])
        image = np.array([
            [[10, 5, 5], [190, 10, 10]],
            [[250, 250, 250], [5, 0, 0]],
        ], dtype=np.uint8)
        pred = colour_only_predict(image, centroids)
        assert pred.shape == (2, 2)
        assert pred[0, 0] == 0   # near-black -> class 0
        assert pred[0, 1] == 1   # near-red -> class 1
        assert pred[1, 0] == 2   # near-white -> class 2
        assert pred[1, 1] == 0   # near-black -> class 0

    def test_chunking_does_not_change_the_result(self):
        """CHUNK bounds memory on large images - verify a chunk boundary
        falling mid-array doesn't corrupt any prediction."""
        from src.segmentation import baselines

        rng = np.random.default_rng(0)
        image = rng.integers(0, 256, size=(3, 7, 3), dtype=np.uint8)  # 21 px
        centroids = np.array([[0.0, 0.0, 0.0], [255.0, 255.0, 255.0]])

        original_chunk = baselines.CHUNK
        try:
            baselines.CHUNK = 21  # whole image in one chunk
            whole = colour_only_predict(image, centroids)
            baselines.CHUNK = 5   # forces multiple chunks, mid-row boundaries
            chunked = colour_only_predict(image, centroids)
        finally:
            baselines.CHUNK = original_chunk

        assert np.array_equal(whole, chunked)
