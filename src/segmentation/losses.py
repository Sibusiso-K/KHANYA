"""Region-based loss for the rare-class failure.

Why this is not the thing petroscope warns against. Their README says class
weighting and loss weighting do NOT resolve mineral class imbalance. That is a
statement about *reweighting the per-pixel cross-entropy term* - each pixel
still competes on equal footing, so a class occupying 1.84% of pixels still
contributes ~1.84% of the gradient signal no matter what constant multiplies it,
and the optimiser's cheapest move remains "never predict the rare class".

Soft Dice changes the shape of the objective rather than its weights. Dice is
computed **per class over the whole batch** and then averaged across classes, so
magnetite's Dice term counts exactly as much as pyrrhotite's despite covering
24x fewer pixels. Predicting no magnetite at all drives that class's Dice to
zero, which is now a large penalty rather than a rounding error.

These are different mechanisms and should not be conflated when writing this up:
we are not claiming petroscope was wrong, we are claiming their warning does not
cover this case.

Used combined with cross-entropy rather than alone. Dice alone is unstable early
in training - its gradient is near-flat while predictions are diffuse - and CE
supplies the reliable early signal.
"""
import torch
from torch import nn


class SoftDiceLoss(nn.Module):
    """Multi-class soft Dice, averaged over classes.

    A class absent from both target and prediction scores Dice ~1 and therefore
    contributes no loss, so empty classes neither help nor hurt. A class absent
    from the target but predicted anyway scores near 0 and is penalised, which
    is the behaviour we want for false positives on rare phases.
    """

    def __init__(self, num_classes: int, smooth: float = 1.0):
        super().__init__()
        self.num_classes = num_classes
        self.smooth = smooth

    def forward(self, logits, target):
        probabilities = logits.softmax(1)
        one_hot = nn.functional.one_hot(target, self.num_classes)
        one_hot = one_hot.permute(0, 3, 1, 2).float()

        # Sum over batch and spatial dims, keeping the class axis: this is what
        # makes each class's term independent of how many pixels it occupies.
        dims = (0, 2, 3)
        intersection = (probabilities * one_hot).sum(dims)
        cardinality = probabilities.sum(dims) + one_hot.sum(dims)
        dice = (2.0 * intersection + self.smooth) / (cardinality + self.smooth)
        return 1.0 - dice.mean()


class CrossEntropyPlusDice(nn.Module):
    """CE for stable early optimisation, Dice for rare-class pressure."""

    def __init__(self, num_classes: int, dice_weight: float = 1.0):
        super().__init__()
        self.cross_entropy = nn.CrossEntropyLoss()
        self.dice = SoftDiceLoss(num_classes)
        self.dice_weight = dice_weight

    def forward(self, logits, target):
        return (self.cross_entropy(logits, target)
                + self.dice_weight * self.dice(logits, target))


def build_loss(name: str, num_classes: int):
    if name == "ce":
        return nn.CrossEntropyLoss()
    if name == "dice":
        return CrossEntropyPlusDice(num_classes)
    raise ValueError(f"unknown loss {name!r}; expected 'ce' or 'dice'")
