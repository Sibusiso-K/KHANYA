# Week-6 backup demo video

This is the offline fallback recording for the talk. It is generated from the same deterministic
`reefprint.viz.demo.offline_demo()` scene used by the Week-5 gate, so the recording cannot drift
from the code that was verified. The two screens are:

1. the three-panel Stokes/analyser physics gate; and
2. the explicit refusal, conservative default, and reason.

Generate it on a laptop with the normal project environment:

```bash
uv run python experiments/004-backup-video/run.py
```

The default output is `output/reefprint-backup-demo.gif`. GIF is intentional: Pillow is already a
declared project dependency, while an MP4 writer would add an ffmpeg installation dependency to a
demo whose defining constraint is one laptop, offline.
