"""single_field_predict()'s shape and refusal contract - not accuracy, which
needs the real trained checkpoint and is covered by the eval scripts, not CI.
"""
import numpy as np
import pytest
import torch
from PIL import Image

from src.segmentation import lumenstone as ls
from src.segmentation.model import build_model, device
from src.segmentation.patches import PATCH, single_field_predict, sliding_window_predict


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


def test_sliding_window_reports_only_completed_tiles(untrained_model):
    model, dev = untrained_model
    image = Image.fromarray(np.zeros((600, 700, 3), dtype=np.uint8))
    events = []
    sliding_window_predict(
        model, image, dev, patch=512, overlap=0,
        progress_callback=lambda *event: events.append(event),
    )
    assert len(events) == 4
    assert [event[0] for event in events] == [1, 2, 3, 4]
    assert all(event[1] == 4 for event in events)
    for _completed, _total, labels, box, confidence in events:
        assert labels.shape == (600, 700)
        assert np.count_nonzero(labels >= 0) > 0
        assert 0.0 <= confidence <= 1.0
        left, top, right, bottom = box
        assert 0 <= left < right <= 700
        assert 0 <= top < bottom <= 600


def test_field_boxes_are_inside_the_image_and_do_not_overlap():
    from src.segmentation.patches import field_boxes
    boxes = field_boxes(3396, 2547)
    assert len(boxes) == 6
    for left, top, right, bottom in boxes:
        assert 0 <= left < right <= 3396 and 0 <= top < bottom <= 2547
        assert (right - left, bottom - top) == (512, 512)
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]


def test_mosaic_keeps_fields_apart_so_particles_cannot_merge():
    import torch
    from src.segmentation.patches import FIELD_GAP, multi_field_predict

    class AllOre(torch.nn.Module):
        def forward(self, x):
            logits = torch.zeros(1, ls.NUM_CLASSES, x.shape[2], x.shape[3])
            logits[:, 1] = 1.0  # every pixel predicted as class 1
            return {"out": logits}

    seen = []
    labels, confidence, mosaic, boxes = multi_field_predict(
        AllOre(), Image.new("RGB", (3396, 2547)), torch.device("cpu"),
        progress_callback=lambda *args: seen.append(args[0]))
    assert seen == [1, 2, 3, 4, 5, 6]
    assert labels.shape == (2 * 512 + FIELD_GAP, 3 * 512 + 2 * FIELD_GAP)
    assert mosaic.size == (labels.shape[1], labels.shape[0])
    assert (labels[:, 512:512 + FIELD_GAP] == 0).all()   # vertical gap is background
    assert (labels[512:512 + FIELD_GAP, :] == 0).all()   # horizontal gap is background
    from src import modal
    assert modal.liberation_stats(labels, labels == 1)[1] == 6  # six separate particles


def test_small_uploads_get_fewer_distinct_fields_never_repeated_crops():
    from src.segmentation.patches import field_boxes, field_coverage
    assert field_boxes(512, 512) == [(0, 0, 512, 512)]
    assert field_coverage(512, 512) == (1, 1.0)
    assert len(field_boxes(1100, 700)) == 2          # 2 columns x 1 row fit
    count, coverage = field_coverage(3396, 2547)
    assert count == 6 and round(coverage, 3) == 0.182
    import random
    rng = random.Random(0)
    for _ in range(200):
        w, h = rng.randint(512, 5000), rng.randint(512, 5000)
        boxes = field_boxes(w, h)                     # raises if any two overlap
        assert len(set(boxes)) == len(boxes)


def _synthetic_dataset(seed=42):
    """A BalancedPatches over two fake 600x700 images, with no file I/O."""
    from src.segmentation.patches import BalancedPatches

    rng = np.random.default_rng(0)
    images = {s: (rng.integers(0, 256, (600, 700, 3), dtype=np.uint8),
                  rng.integers(0, ls.NUM_CLASSES, (600, 700), dtype=np.int64))
              for s in ("a", "b")}
    index = {(s, c): [(int(y), int(x)) for y, x in zip(rng.integers(0, 600, 50), rng.integers(0, 700, 50))]
             for s in images for c in range(ls.NUM_CLASSES)}
    shapes = {s: (600, 700) for s in images}
    ds = BalancedPatches(sorted(images), index, shapes, length=8, train=True, seed=seed)
    ds._image = lambda stem: images[stem]
    return ds


def test_training_patches_are_reproducible_from_seed_and_epoch():
    """The unseeded train sampler made the recipe irreproducible (0.5725 vs
    0.4543 on a re-run). Same seed and epoch must now give identical patches;
    a new epoch must give new ones."""
    first, second = _synthetic_dataset(), _synthetic_dataset()
    for ds in (first, second):
        ds.set_epoch(3)
    for i in range(8):
        x1, y1 = first[i]
        x2, y2 = second[i]
        assert torch.equal(x1, x2) and torch.equal(y1, y2)

    first.set_epoch(4)
    assert any(not torch.equal(first[i][1], second[i][1]) for i in range(8))
