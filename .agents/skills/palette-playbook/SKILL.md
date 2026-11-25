---
name: palette-playbook
description: Keep palette behavior in sync across the Material Notes Anki add-on, interactive demo, CSS, documentation, and release packages.
---

# Palette Playbook

Use this skill as the authoritative workflow for adding, replacing, or changing a palette in this repository. Keep this file and the palette parity test in sync whenever the palette catalog changes.

## Source of truth

| Surface | Source |
| --- | --- |
| Add-on names and finish availability | `__init__.py` (`COLORS`, `PALETTE_NAMES`, `FINISHES`, `available_finishes`) |
| Demo palette picker and selected finish | `index.html`, `src/js/main.js` |
| Palette properties and class aliases | `src/styles/variants.css` |
| Generated CSS and demo card setup data | `models/styles.css`, `src/js/card-setup-sources.js` via `make build-css` |
| Public style tag catalog and usage | `docs/using-style-tags.md` |
| User-facing features and release notes | `README.md`, `CHANGELOG.md`, `manifest.json` |
| Cross-surface parity | `tests/test_styles.py` |

Never edit generated CSS or card setup source files directly. Update source files first, then run the documented build.

## Palette change workflow

1. Record the palette’s UI name, slug, light and dark header colors, foreground colors, fills, outline behavior, finish set, generated classes, alias classes, and migration behavior in the truth matrix below.
2. Update the add-on palette catalog and finish availability in `__init__.py`. Handle saved appearance values deliberately; when replacing a palette, normalize managed saved settings while removing the old CSS and UI alias.
3. Update the website palette picker and finish logic in `index.html` and `src/js/main.js`.
4. Add CSS values and selectors for every supported finish and the `Material::` class alias in `src/styles/variants.css`. Use shared palette custom properties so light and dark mode resolve consistently. Keep header colors independent from Filled and Outlined card fills when the design requires it.
5. Update prose in `README.md`, `docs/using-style-tags.md`, and `CHANGELOG.md`. Regenerate the catalog in `docs/using-style-tags.md`; do not hand-edit rows inside its generated markers.
6. Add or update the CI-discoverable parity test in `tests/test_styles.py`. It must compare the add-on palette and finish contract, demo picker, and generated stylesheet tags.
7. Bump `manifest.json` for a user-visible palette change and update the release notes. Invalidate changed static asset URLs in `index.html`.
8. Run the exact validations below. Confirm generated catalogs and assets are current, and report skipped runtime validation.

## Truth matrix for Inverted

| Palette | Mode | Question header | Header text | Finishes | Palette tag | Finish tags |
| --- | --- | --- | --- | --- | --- | --- |
| Inverted | Light | Black | White | Base, Filled, Outlined | `note-inverted` | `note-inverted-base`, `note-inverted-filled`, `note-inverted-outlined` |
| Inverted | Dark | White | Black | Base, Filled, Outlined | `note-inverted` | `note-inverted-base`, `note-inverted-filled`, `note-inverted-outlined` |

Each tag also has a `Material::` prefixed form. There is no White palette or White style tag. Managed saved settings with `palette: "white"` migrate to `palette: "inverted"` when styles are refreshed or edited.

## Required validations

Run these commands from the repository root, in order:

```sh
make build-css
make test
make build-card
make build-addon
git diff --check
```

`make build-css` updates `models/styles.css`, `src/js/card-setup-sources.js`, and the generated style tag catalog. `make test` includes the palette parity test. `make build-card` and `make build-addon` verify both release exports.
