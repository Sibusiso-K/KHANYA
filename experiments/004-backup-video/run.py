"""Render the offline Week-5 scene as a self-contained backup demo video.

    uv run python experiments/004-backup-video/run.py

The output is an animated GIF rather than an MP4 so the backup can be generated on a clean
laptop without ffmpeg. It contains the physics gate, the visible geometry refusal, and — added
2026-09-15, Workstream E — the plant-parameter advisory screen: an advisory applied, then a
second, stale one explicitly refused. Regenerated whenever `offline_demo()`'s scene changes;
before this session the GIF only knew about the first two screens and silently missed the third.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from matplotlib.backends.backend_agg import FigureCanvasAgg
from PIL import Image

from reefprint.viz.demo import offline_demo


def _figure_image(figure) -> Image.Image:  # noqa: ANN001
    canvas = FigureCanvasAgg(figure)
    canvas.draw()
    width, height = canvas.get_width_height()
    return Image.frombuffer(
        "RGBA", (width, height), canvas.buffer_rgba(), "raw", "RGBA", 0, 1
    ).copy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).parent / "output" / "reefprint-backup-demo.gif",
    )
    parser.add_argument("--seconds-per-screen", type=float, default=4.0)
    args = parser.parse_args()
    if args.seconds_per_screen <= 0:
        parser.error("--seconds-per-screen must be positive")

    demo = offline_demo()
    screens = [_figure_image(demo.gate), _figure_image(demo.refusal), _figure_image(demo.advisory)]
    # GIF frames share a canvas: preserve the taller refusal, including its reason.
    size = (max(screen.width for screen in screens), max(screen.height for screen in screens))
    padded = []
    for screen in screens:
        frame = Image.new("RGBA", size, "white")
        frame.paste(screen, ((size[0] - screen.width) // 2, (size[1] - screen.height) // 2))
        padded.append(frame)
    screens = padded
    # Ten frames per screen keeps common players from treating a short GIF as a still image.
    duration_ms = round(args.seconds_per_screen * 1000 / 10)
    frames = [screen for screen in screens for _ in range(10)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        args.output,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        disposal=2,
    )
    print(f"backup video     {args.output}")
    print(f"screens          {len(screens)} x {args.seconds_per_screen:g}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
