import torch
from torchvision.models.segmentation import deeplabv3_resnet50, DeepLabV3_ResNet50_Weights


def build_model(num_classes: int = 2, pretrained: bool = True):
    """DeepLabv3+ResNet50, matching the method used in the published FeM paper
    (Filippo et al. 2021) for reflected-light ore/resin segmentation."""
    weights = DeepLabV3_ResNet50_Weights.DEFAULT if pretrained else None
    model = deeplabv3_resnet50(weights=weights)
    model.classifier[4] = torch.nn.Conv2d(256, num_classes, kernel_size=1)
    if model.aux_classifier is not None:
        model.aux_classifier[4] = torch.nn.Conv2d(256, num_classes, kernel_size=1)
    return model


def device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")
