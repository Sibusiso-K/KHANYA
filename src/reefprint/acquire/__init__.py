"""Acquisition: analyser rotation, LED sequencing, camera control.

Owns the week-1 gate's input half: driving a rotating analyser through a series of angles and
returning a calibrated intensity stack.

Constraint from gauntlet blind spot 6 — **adaptive illumination is a leakage channel**.
Acquisition state correlates with collection time, which correlates with labels. The
illumination schedule is frozen for everything that becomes training data; adaptivity is
inference-only, and the schedule used is recorded in the acquisition metadata either way.
"""
