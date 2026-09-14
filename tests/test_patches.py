"""single_field_predict()'s shape and refusal contract - not accuracy, which
needs the real trained checkpoint and is covered by the eval scripts, not CI.
"""
import numpy as np
import pytest
from PIL import Image

from src.segmentation import lumenstone as ls
from src.segmentation.model import build_model, device
from src.segmentation.patches import PATCH, single_field_predict


@pytest.fixture(scope="module")
def untrained_model():
    """An untrained model is enough to check shapes and the refusal
    contract - accuracy needs the real checkpoint, out of scope for a unit
    test that must run without one."""
    dev = device()
    model = build_model(num_classes=ls.NUM_CLASSES, pretrained=False).to(dev)
    model.eval()
    return model, dev


class TestSingleFieldPredict:
    def test_returns_a_patch_sized_prediction_and_a_matching_crop(self, untrained_model):
        model, dev = untrained_model
        image = Image.fromarray(
            np.random.default_rng(0).integers(0, 256, size=(900, 1200, 3), dtype=np.uint8)
        )
        labels, mean_confidence, cropped = single_field_predict(model, image, dev)

        assert labels.shape == (PATCH, PATCH)
        assert cropped.size == (PATCH, PATCH)
        assert 0.0 <= mean_confidence <= 1.0

    def test_refuses_an_image_smaller_than_the_field(self, untrained_model):
        model, dev = untrained_model
        image = Image.fromarray(
            np.random.default_rng(0).integers(0, 256, size=(200, 300, 3), dtype=np.uint8)
        )
        with pytest.raises(ValueError, match="smaller than"):
            single_field_predict(model, image, dev)

    def test_the_crop_is_centred(self, untrained_model):
        """A centre crop, not a corner crop - the field should sit in the
        middle of a larger image, not against one edge."""
        model, dev = untrained_model
        width, height = 1200, 900
        array = np.zeros((height, width, 3), dtype=np.uint8)
        expected_top, expected_left = (height - PATCH) // 2, (width - PATCH) // 2
        array[expected_top:expected_top + PATCH, expected_left:expected_left + PATCH] = 255
        image = Image.fromarray(array)

        _labels, _confidence, cropped = single_field_predict(model, image, dev)
        assert np.array(cropped).min() == 255  # the whole crop is the white region
