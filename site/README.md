# Website

This page follows the Amplifier Smart Tools family's static Python build, visual
language, two-column hero, local assets, fine rules, and restrained navigation.
The generated `_site/` directory works on any static host, including a repository
subpath on GitHub Pages. All product links are relative or page anchors.
`.github/workflows/pages.yml` builds, checks, and publishes `_site/` from `main`.

## Build and preview

From the repository root with Python 3.11 or later:

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8000 --bind 127.0.0.1 --directory _site
```

Open `http://127.0.0.1:8000`. The build uses only Python's standard library.

## Edit

- `site.json`: metadata and explicitly fictional runs, each with a usefulness card
  (six criteria, start and end, rating and evidence), a per-checkpoint builder trace
  (1 Early, 2 Developing, 3 Strong), labeled dips, a return check, and a decision log.
  The build refuses a labeled dip that isn't a drop, and computes each run's zone
  with the skill's rule.
- `template.html`: semantic page content and layout.
- `style.css`: product styles and responsive behavior on top of the family theme.
- `site.js`: switching runs, the in-browser scorer (same zone rule, stores and sends
  nothing), and copy feedback. Every run is rendered at build time, so the page reads
  fully without JavaScript.
- `assets/`: original SVG favicon and share illustration.
- `../skills/worth-using/references/rubric.md` and `../docs/BENCHMARK.md`: the source
  for the criteria, evidence grades, opening questions, dimensions, teaching moves,
  diagnosis, and benchmark rows.
  Do not fork the method into another content file.

## Theme provenance

`theme/style.css` is an unmodified snapshot of the Amplifier Smart Tools family theme
v0.1.0. `theme/LICENSE` keeps its original MIT notice. The product template, trace,
SVG assets, and styles are new.

## Design notes

- Paper `#f6f4ee`, ink `#252823`, muted `#64685e`, rules `#d8d8cc`, gold `#80642f`
  from the family; moss accent `#3f6b4a` and rust `#8a5446` for Missing ratings.
- Georgia headings and Arial body, system fallbacks, no font requests.
- The builder's trace and the usefulness card are the expressive elements. Gold rings
  mark dips.
- No automatic movement. Reduced motion is respected.

## Deployment

The Pages source is GitHub Actions. The workflow separates build and deployment,
checks the output before upload, and uploads only `_site/`. Keep asset, navigation,
and download paths relative so repository-subpath hosting works.
