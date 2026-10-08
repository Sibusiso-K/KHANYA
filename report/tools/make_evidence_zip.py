"""Build report/evidence/REEFPRINT_report_evidence_v17.zip. Run from report/."""
import hashlib, json, subprocess, sys, zipfile, platform

COMMIT = "ab333071d184fa8f853ea96e78fd81a2f948d547"
INPUTS = ["training/hidsag-v6-live-20261001/output/hidsag_v6_results.json",
          "training/hidsag-v8-model-20261002/output/hidsag_v8_model_results.json"]
files = {
    "PILOT_COST_LEDGER.csv": open("PILOT_COST_LEDGER.csv", "rb").read(),
    "make_ledger.py": open("tools/make_ledger.py", "rb").read(),
    "replay_envelope.py": open("tools/replay_envelope.py", "rb").read(),
    "replay_envelope.json": open("evidence/replay_envelope.json", "rb").read(),
    "EVIDENCE_MANIFEST.md": open("EVIDENCE_MANIFEST.md", "rb").read(),
}
for p in INPUTS:
    files["inputs/" + p] = subprocess.check_output(["git", "show", f"{COMMIT}:{p}"])
out = json.load(open("evidence/replay_envelope.json"))
readme = f"""# REEFPRINT/KHANYA report evidence package (v17, 8 October 2026)

Supports report v17 (report/main.tex). Planning allowances are not quotes; software checks are not accuracy results.

## Contents
- PILOT_COST_LEDGER.csv: every pilot cost line with tranche, proposed payer, release condition, commitment point,
  cancellation exposure and contingency; P0 broken into its six allowances (cap R210,000, outside the pilot total).
  Regenerate with `python make_ledger.py` (from report/). Tranche totals: L1 R1,748,267; L2 R2,720,533; R-H R472,320;
  R-M R787,200; reserves R1.679-2.171M; B1 R0.57-0.90M; B2 R2.71-4.35M; pilot R10.69-13.15M; with P0 R10.90-13.36M.
  Released cash = tranches released at their gates; committed/non-recoverable = orders placed, notice periods, lease
  deposit and cancellation; avoidable = unreleased tranches and reserves.
- replay_envelope.py / replay_envelope.json: envelope-clipped feed-rate replay (report Section 4.2).
  Inputs: inputs/training/... extracted verbatim from commit {COMMIT} (branch codex/pwa-phase-roadmap).
  Policy: deployed policy of training/value-chain-20261002/value_chain.py (refused -> fold P90; borderline ->
  max(bound, P90); pass -> one-sided 90% bound); feed clipped to 85-110% of design (hardness clipped to
  [P90/1.10, P90/0.85]). Throughput vs blind P90 = sum(P90)/sum(Wi_used) - 1. Bootstrap: units = samples
  (no drill-hole ids), B = 4000, numpy default_rng seed 1, percentile 2.5/97.5. Rounded to 0.1 percentage point.
  Result: unclipped {out['deployed_unclipped']['throughput_vs_blind_p90']*100:.2f}% {[round(x*100,2) for x in out['deployed_unclipped']['ci95']]} (reproduces the committed value);
  clipped {out['deployed_envelope_85_110']['throughput_vs_blind_p90']*100:.2f}% {[round(x*100,2) for x in out['deployed_envelope_85_110']['ci95']]}.
  Run by Claude on 8 Oct 2026 with Python {platform.python_version()}; the script reads inputs with `git show` from the repository root.
- EVIDENCE_MANIFEST.md: checkpoint hashes, release index (historical model, tested local build, public static demo,
  research datasets) and local packages, with items still missing marked.
- SHA256SUMS: checksums of every file above.
"""
files["README.md"] = readme.encode()
sums = "".join(f"{hashlib.sha256(v).hexdigest()}  {k}\n" for k, v in sorted(files.items()))
files["SHA256SUMS"] = sums.encode()
with zipfile.ZipFile("evidence/REEFPRINT_report_evidence_v17.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for k, v in files.items():
        z.writestr(k, v)
print(sums)
print("zip sha256", hashlib.sha256(open("evidence/REEFPRINT_report_evidence_v17.zip", "rb").read()).hexdigest())
