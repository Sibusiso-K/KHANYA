"""Week-1 gate: rotation series in, anisotropy map out, pentlandite dark and pyrrhotite lit.

    uv run python experiments/001-week1-gate/run.py

Writes the figure to ``output/week1-gate.png`` and prints the numbers behind it. The numbers
matter more than the picture: a colour map can be talked into showing anything, a table of
per-phase DOLP with the projection rate next to it cannot.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reefprint.acquire.phantom import synthetic_rotation_series
from reefprint.polarim.stokes import stokes_from_rotation_series
from reefprint.viz.anisotropy import anisotropy_figure


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noise", type=float, default=0.25, help="Gaussian noise sigma, in R%%.")
    parser.add_argument("--angles", type=int, default=36, help="Analyser positions over 180 deg.")
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "output")
    args = parser.parse_args()

    phantom = synthetic_rotation_series(
        n_angles=args.angles, shape=(192, 256), noise_pct=args.noise, seed=args.seed
    )

    # Unprojected first, so the escape rate can be *measured* rather than hidden by the fix.
    raw = stokes_from_rotation_series(phantom.series.frames, phantom.series.angles_rad)
    stokes = raw.project_to_physical()
    escaped = float((~raw.is_physical).mean())

    print(f"source            {phantom.series.source}")
    print(f"frames            {phantom.series.n_angles} x {phantom.series.shape}")
    print(f"units             {phantom.series.units}")
    print(f"off-cone pixels   {escaped:.2%}  (noise pushing the fit outside S0 >= |S1,S2|)")
    print(f"residual RMS      {stokes.residual_rms.mean():.4f} {phantom.series.units}")
    print()
    print(f"{'phase':<14}{'true R%':>9}{'fitted S0':>11}{'true DOLP':>11}{'fitted DOLP':>13}  src")
    for phase in phantom.phases:
        pixels = phantom.mask(phase.name)
        flag = "measured" if phase.is_measured else "PLACEHOLDER"
        print(
            f"{phase.name:<14}{phase.reflectance_pct:>9.2f}{stokes.s0[pixels].mean():>11.2f}"
            f"{phase.anisotropy:>11.3f}{stokes.anisotropy[pixels].mean():>13.3f}  {flag}"
        )

    pentlandite = float(stokes.anisotropy[phantom.mask("pentlandite")].mean())
    pyrrhotite = float(stokes.anisotropy[phantom.mask("pyrrhotite")].mean())
    print()
    print(f"GATE  pyrrhotite / pentlandite anisotropy = {pyrrhotite / pentlandite:.1f}x")

    args.output.mkdir(parents=True, exist_ok=True)
    destination = args.output / "week1-gate.png"
    figure = anisotropy_figure(
        phantom.series,
        stokes,
        labels=phantom.labels,
        phase_names={p.label: p.name for p in phantom.phases},
        title=(
            f"REEFPRINT week-1 gate — synthetic phantom, {args.angles} analyser positions, "
            f"noise {args.noise} R%"
        ),
    )
    figure.savefig(destination, dpi=150)
    print(f"figure            {destination}")

    # Not an assertion: this script reports, it does not gate. tests/test_polarim.py gates.
    if not (pentlandite < 0.02 < pyrrhotite):
        print("\nWARNING: the gate condition does not hold on this run.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
