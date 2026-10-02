---
title: REEFPRINT Live
emoji: ⛏️
colorFrom: indigo
colorTo: yellow
sdk: docker
app_port: 7860
pinned: true
license: other
short_description: Belt-to-decision mineral characterisation demo (Team Sonar)
---

# REEFPRINT · KHANYA: Live

**Open the app full screen: https://lethabomh14-reefprint.hf.space/?guest=1**

Built by Team Sonar for the Mintek–SCi Grad Hackathon 2026 (Problem 3: Computer Vision for Real-Time Mineralogical Characterisation).

## What this is

- **The data:** replays of real public data in three labelled tracks:
  - HIDSAG hyperspectral (CC0);
  - Bushveld chromitite assays (Bachmann et al. 2019, CC BY 4.0);
  - a Brazilian iron-ore flotation plant (CC0).
- **Not connected to any plant.** Decisions are recorded in a **guest sandbox that resets daily**.
- **What you can try:**
  - scan a parcel;
  - approve a feed-rate proposal inside its envelope;
  - verify the hash-chained record and download a signed checkpoint (Ed25519 + ML-DSA-65, post-quantum);
  - import a lab CSV;
  - upload a photo (EXIF stripped, encrypted at rest, deleted after 24 h);
  - ask the offline assistant.

Staff accounts are created by the team only. There is no web admin.

## Limits

- **Restarts:** the Space sleeps after 48 h with no visitors, and wakes in about a minute. A restart clears the sandbox and generates new signing keys. A checkpoint downloaded earlier still carries the public keys it was signed with.
- **No external AI service is called;** the assistant routes questions offline.

Source: `presentation/belt-monitor/` on the team repository. Security design: `docs/19-security-by-design.md`.
