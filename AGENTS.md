# AGENTS.md

## Cursor Cloud specific instructions

This repo is a single, dependency-free static HTML landing page (Japanese debt-reduction "無料減額シミュレーター" marketing LP). There is no package manager, build step, backend, or database.

- Source of truth: `index.html` (all HTML/CSS/JS inline), `img/*.png` assets, and `vercel.json` (Vercel static hosting + routing config).
- Run locally (dev): serve the static files from the repo root, e.g. `python3 -m http.server 8000`, then open `http://localhost:8000/`. Any static server works (`npx serve`, `npx vercel dev`, etc.).
- No lint/test/build commands exist for this repo. There is nothing to compile or transpile; changes to `index.html` are reflected on browser refresh.
- Interactivity is vanilla JS in `index.html`: the `toggle()` accordion "choice" chips and an exit-intent popup (`#exitPopup`, shown on mouseleave/back-navigation).
- External dependency (not runnable locally): all CTA buttons and the popup link out to the third-party form at `https://saimucheck.com/page/s002/...`. The full lead funnel cannot be exercised locally.
- Google Fonts (Noto Sans JP) load via CDN; the page still renders with fallback system fonts if the CDN is blocked.
