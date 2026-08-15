"""Calibration: reflectance standards, R% conversion, QDF lookup.

Converts raw camera counts to quantitative specular reflectance R% against a standard, and
looks published values up in the IMA/COM Quantitative Data File.

The QDF is the teacher. Every R% this project reports must be traceable to a standard and a
wavelength, never to a model's opinion (CLAUDE.md Rule 1 and Rule 6).
"""
