# Dashboard build step (dev machine only, never on the demo laptop)

This directory compiles a static, offline CSS bundle from
`dashboard/templates/khanya.html.jinja`. It is **not** a runtime dependency -
`dashboard/render.py` reads the compiled output from `dashboard/static/` and
inlines it. Node/npm are never imported by anything under `src/` or
`dashboard/app.py`, and nothing here runs when the dashboard runs.

Regenerate the compiled CSS whenever the template's Tailwind classes change:

```bash
cd dashboard/build
npm install          # first time only; node_modules/ is gitignored
npx tailwindcss -i input.css -o ../static/tailwind.css --minify
```

`tailwind.config.js`'s `colors`/`boxShadow`/`animation` values are the real
Mintek design tokens (see HANDOVER entry 36/37) - if the brand palette ever
changes, edit them there, not by hand-patching the compiled CSS.

Fonts (`dashboard/static/fonts/*.ttf`) are vendored once from Google Fonts'
own static CDN (Plus Jakarta Sans, JetBrains Mono - both SIL Open Font
License) and checked in; they do not need to be regenerated unless a new
weight is needed.
