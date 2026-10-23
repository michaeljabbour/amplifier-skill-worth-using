# Working on Worth Using

- Read `skills/worth-using/SKILL.md` and its `references/rubric.md` before changing
  the method. Record any change in CHANGELOG.md.
- Keep the six criteria independent and never add them up. Keep each rating separate
  from its evidence grade. Never upgrade evidence: Seen needs someone outside the team.
- Keep the five builder dimensions independent; never combine them into one score.
- The tool and the builder are reported separately. Never smooth a growth trace.
- Team scoring collects ratings before any reveal and never averages.
- Never claim research, users, usage, benchmark results, or deployment without evidence.
  `docs/BENCHMARK.md` is a plan until a dated record exists under `docs/evaluations/`.
- The site is static Python, HTML, CSS, and JavaScript. Keep it free of runtime
  dependencies, external fonts, analytics, and backend services. The scorer stores
  and sends nothing.
- The Amplifier bundle is `bundle.md`, `behaviors/`, `modes/`, and `recipes/`. Keep the
  mode body short (it is injected every turn) and the method in the skill, not copied
  into the mode or recipe. Validate the recipe with the `recipes` tool after edits.
- Keep only one file named `SKILL.md` in the repository; snapshots use another name.
- Content is in `site/site.json` and `site/template.html`; criteria, evidence grades,
  questions, dimensions, teaching moves, diagnosis rows, and benchmark rows are read
  from the rubric reference and `docs/BENCHMARK.md` at build time.
- Keep the MIT notice in `site/theme/LICENSE`. Do not imply institutional affiliation.
- Examples are fictional and must say so. Do not use internal product names.
- Voice: verdict first, one question per turn, light humor never at the user.
- Use plain words, visible labels, keyboard controls, and reduced-motion support.
- Run `python3 scripts/build.py`, `python3 scripts/check.py`, and
  `node --check site/site.js`. Inspect desktop and phone layouts after UI changes.
- Do not add a remote, push, publish, deploy, or contact anyone unless asked.
