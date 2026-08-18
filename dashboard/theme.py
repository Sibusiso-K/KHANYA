KHANYA_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&display=swap');

:root {
  --ink: #e8e3d8;
  --dim: #8a8378;
  --bg: #14120f;
  --panel: #1c1915;
  --line: #3a352c;
  --amber: #ff9d2e;
  --amber-dim: #cc7d1f;
  --ok: #6fae5c;
  --warn: #d6a92c;
  --bad: #c85a4a;
}

html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace !important; }
.stApp { background: var(--bg); color: var(--ink); }

/* kill Streamlit's rounded, gradient, generic chrome */
.block-container { padding-top: 2rem; max-width: 1180px; }
#MainMenu, footer, header { visibility: hidden; }

h1, h2, h3 { font-weight: 800 !important; letter-spacing: -0.01em; color: var(--ink) !important; }

.khanya-mast {
  border: 1px solid var(--line); border-left: 4px solid var(--amber);
  background: var(--panel); padding: 1.1rem 1.4rem; margin-bottom: 1.6rem;
}
.khanya-mast .tag {
  font-size: 0.72rem; letter-spacing: 0.18em; color: var(--amber);
  text-transform: uppercase; font-weight: 700;
}
.khanya-mast .title { font-size: 1.6rem; font-weight: 800; margin: 0.15rem 0 0.1rem; }
.khanya-mast .sub { font-size: 0.82rem; color: var(--dim); }

.khanya-panel {
  border: 1px solid var(--line); background: var(--panel);
  padding: 1rem 1.2rem; margin-bottom: 1rem;
}
.khanya-panel .head {
  font-size: 0.72rem; letter-spacing: 0.14em; color: var(--dim);
  text-transform: uppercase; border-bottom: 1px solid var(--line);
  padding-bottom: 0.5rem; margin-bottom: 0.7rem; font-weight: 700;
}

.khanya-readout {
  display: flex; justify-content: space-between; align-items: baseline;
  padding: 0.35rem 0; border-bottom: 1px dashed var(--line); font-size: 0.88rem;
}
.khanya-readout:last-child { border-bottom: none; }
.khanya-readout .k { color: var(--dim); }
.khanya-readout .v { color: var(--ink); font-weight: 700; font-variant-numeric: tabular-nums; }

.khanya-verdict {
  border: 1px solid var(--line); border-left: 5px solid var(--ok);
  background: var(--panel); padding: 1rem 1.3rem;
}
.khanya-verdict.warn { border-left-color: var(--warn); }
.khanya-verdict.bad { border-left-color: var(--bad); }
.khanya-verdict .action {
  font-size: 1.15rem; font-weight: 800; letter-spacing: -0.01em;
}
.khanya-verdict .reason { color: var(--dim); font-size: 0.85rem; margin-top: 0.4rem; line-height: 1.5; }

.khanya-band {
  height: 6px; background: var(--line); position: relative; margin: 0.6rem 0 0.3rem;
}
.khanya-band .zone {
  position: absolute; top: 0; bottom: 0; background: rgba(214,169,44,0.35);
}
.khanya-band .marker {
  position: absolute; top: -4px; width: 2px; height: 14px; background: var(--amber);
}
.khanya-band .thresh {
  position: absolute; top: -4px; width: 1px; height: 14px; background: var(--dim);
}

[data-testid="stFileUploaderDropzone"] {
  background: var(--panel) !important; border: 1px dashed var(--line) !important;
  border-radius: 0 !important;
}
.stButton>button, [data-testid="stFileUploader"] button {
  border-radius: 0 !important; border: 1px solid var(--amber-dim) !important;
  color: var(--amber) !important; background: transparent !important;
  font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important;
}
[data-testid="stMetricValue"] { color: var(--amber) !important; font-weight: 800 !important; }
[data-testid="stMetricLabel"] { color: var(--dim) !important; text-transform: uppercase; font-size: 0.7rem !important; letter-spacing: 0.1em; }
[data-testid="stImage"] img { border: 1px solid var(--line); }
.stAlert { border-radius: 0 !important; }
</style>
"""
