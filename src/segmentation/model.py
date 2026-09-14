import torch
from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights


def build_model(num_classes: int = 2, pretrained: bool = True):
    """Torchvision DeepLabV3 with a ResNet-50 backbone.

    This calls ``torchvision.models.segmentation.deeplabv3_resnet50``. It is
    DeepLabV3, not DeepLabV3+; keep the exact name consistent in the UI,
    accuracy report and pitch.
    """
    # aux_loss explicit and constant: torchvision only attaches the aux
    # classifier head when aux_loss is truthy, and its default depends on
    # `weights`, so pretrained=True vs False silently build different
    # architectures unless this is pinned - which is what broke checkpoint
    # loading (train pretrained=True, eval pretrained=False).
    #
    # Pinned to the explicit enum, not .DEFAULT: as of torchvision 0.28,
    # .DEFAULT resolves to COCO_WITH_VOC_LABELS_V1 (the only member this
    # enum has), but a future torchvision release could add a member and
    # repoint DEFAULT at it, silently changing which pretrained weights the
    # shipped checkpoint was fine-tuned from without anyone noticing (the
    # 2026-09-12 review's exact ask - "pin the explicit enum and checkpoint
    # hash rather than DEFAULT"). Record in SBOM.md if this enum member ever
    # changes.
    weights = DeepLabV3_ResNet50_Weights.COCO_WITH_VOC_LABELS_V1 if pretrained else None
    # torchvision otherwise defaults weights_backbone to ImageNet weights even
    # when weights=None. Evaluation loads our checkpoint and must never fetch a
    # backbone from the network first. Full pretrained weights include it already.
    model = deeplabv3_resnet50(
        weights=weights, weights_backbone=None, aux_loss=True
    )
    model.classifier[4] = torch.nn.Conv2d(256, num_classes, kernel_size=1)
    if model.aux_classifier is not None:
        model.aux_classifier[4] = torch.nn.Conv2d(256, num_classes, kernel_size=1)
    return model


def device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
