---
bundle:
  name: worth-using
  version: 0.1.0
  description: >-
    Scores whether a tool is genuinely useful to someone who didn't build it, and
    coaches the builder to close the gaps: the worth-using skill, a /useful
    working mode, and a staged, human-gated recipe.

# Thin root: a lean host plus this bundle's behavior. Most users should add only
# the behavior to their existing host (see README).
includes:
  - bundle: git+https://github.com/microsoft/amplifier-foundation@main#subdirectory=bundles/anchors/bundle.md
  - bundle: worth-using:behaviors/worth-using
---

@anchors:context/system.md
