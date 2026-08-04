import torch
from torchvision import models

from . import config


def build_model(num_classes: int = len(config.CLASSES), pretrained: bool = True):
    """ResNet18 baseline. Small enough to train on a laptop GPU or CPU overnight.

    Swap for a segmentation model (DeepLabv3+ / Mask R-CNN) in weeks 4-5 once the
    classification baseline has an honest number attached to it.
    """
    weights = models.ResNet18_Weights.DEFAULT if pretrained else None
    model = models.resnet18(weights=weights)
    model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
    return model


def device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
