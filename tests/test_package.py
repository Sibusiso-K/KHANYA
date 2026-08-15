"""The one suite that must always be green.

Everything else under ``tests/`` is a ``placeholder`` marker until its module exists. This file
is the floor: the package imports, the layout matches the constitution, and CI has a real
signal to go red on.
"""

from __future__ import annotations

import importlib

import pytest

import reefprint

MODULES = (
    "acquire",
    "calibrate",
    "polarim",
    "segment",
    "texture",
    "heads",
    "trust",
    "integrate",
    "viz",
)


def test_version_is_set():
    assert reefprint.__version__


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    """Every module in the CLAUDE.md repo layout exists and imports cleanly."""
    importlib.import_module(f"reefprint.{name}")


@pytest.mark.parametrize("name", MODULES)
def test_module_documents_itself(name):
    """A module docstring is not decoration here.

    It is where the constraint that governs the module is written down, so the next session
    reads it before touching the code.
    """
    module = importlib.import_module(f"reefprint.{name}")
    assert module.__doc__, f"reefprint.{name} has no docstring"
