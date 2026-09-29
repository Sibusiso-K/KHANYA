# Copy-paste prompt for a new chat

**September 29 update:** the build-ready plan is now [README.md](README.md), and the current implementation prompt is at the end of [LUNA-IMPLEMENTATION.md](LUNA-IMPLEMENTATION.md). The user explicitly approved retraining the missing S2 model. Use that newer prompt for Luna. The investigation prompt below is retained as historical context.

```text
Continue my KHANYA / REEFPRINT investigation for the Mintek SCi hackathon, Problem 3: Computer Vision for Real-Time Mineralogical Characterisation.

First read:
C:\Users\USER\Desktop\REEFPRINT\handover\KHANYA-RESEARCH-HANDOVER-2026-09-29.md
C:\Users\USER\Desktop\REEFPRINT\handover\KHANYA-HACKATHON-STRATEGY-2026-09-29.md
C:\Users\USER\Desktop\REEFPRINT\handover\KHANYA-TOOLS-AND-PIPELINE-2026-09-29.md
C:\Users\USER\Desktop\REEFPRINT\handover\KHANYA-CHEMISTRY-TO-3D-EXTENSION-2026-09-29.md

Repo: https://github.com/Sibusiso-K/KHANYA

We have no XRF, microscope rig or other instruments. We need public research data, free/open-source software and honest simulation. The required deliverables are a trained tool identifying at least three mineral phases, an accuracy report, and a demonstration of how its outputs adjust plant parameters. I want the most impressive scientifically defensible result we can deliver, and I am open to a well-supported pivot. Do not guarantee a win or claim global novelty without evidence.

The previous investigation recommends retaining the existing DeepLabV3–ResNet-50 microscopy core and showing chalcopyrite, pentlandite and pyrrhotite from LumenStone S2. The proposed distinctive demonstration connects image quality, phase/association evidence, decision uncertainty, real local OPC UA messaging and a simulated control response. A proposed quality gate and decision-sensitivity overlay are not built yet. My latest interest is a bounded chemistry-to-geographical-3D extension: public assay replay or import to a phone/laptop sample record, automatically updating real sample markers on real terrain. Read the extension design. The local Bushveld CSV has chemistry and depth intervals but no geographic collar coordinates/surveys; do not fabricate them. LumenStone and these assays are not paired samples. More advanced underground modelling still needs additional evidence.

Do not repeat broad research already recorded. Check the current repository state and preserve any changes made since the handover. The local REEFPRINT checkout's branch named main is not the KHANYA application history. The live KHANYA main head verified on September 29 was 9181668cffd9350211a9a8a2cf0b44c80f8deaee, but recheck it. The GitHub connector returned 404; the configured authenticated gh CLI succeeded for read-only access. Do not merge the separate histories.

Start by giving me a concise assessment of what is already implemented, what remains hypothetical, and the single next action with the highest value. Continue the investigation/design from there. If I ask you to build, first verify the actual checkpoint, dataset and working inference path, then implement the smallest complete model-output-to-simulated-process-control demonstration. Acknowledging observation values is not yet a plant-parameter change.

Preserve the handover's evidence limits: the magnetite failure, lighting sensitivity, corrected evaluation protocols, 2D association versus true liberation, Norilsk data versus South African ore, and simulated control versus validated plant recovery. Use fresh held-out evaluation for new improvements and report refusals alongside accepted-case errors. No invented results, kinetics, ore bodies or calibrated doses. Keep the offline demo working. Update the handover as new findings or changes occur.
```

If continuing on another computer, attach the four referenced Markdown files and replace the local paths with their new locations. The handover records the required repository references and sources.
