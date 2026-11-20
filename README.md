# Material Notes for Anki

Material-style flashcards for Anki with light and dark modes. In the [interactive demo](https://anki-material-notes.netlify.app), choose a color or country palette, then choose an available finish. Use the **Show answer** icon to reveal or hide the answer. Under **Source code**, select the **Front** or **Back** tab to see the corresponding HTML.

## Use the add-on

Open **Tools → Material Notes…** to see the Material note types in the current collection. **Create note type…** lets you choose **Basic** or **Multiple choice** and name the new type.

**Update note types** refreshes the card templates and styling of the listed types in place. If you edited the templates or styling, the add-on asks before replacing your changes. Existing notes keep their field values.

## Copy a card into Anki

Open **Cards…** for a Basic note type with the **Front** and **Back** fields. Copy the contents of each file into the corresponding editor pane.

Download a versioned copy of the three files, together or individually, from [GitHub Releases](https://github.com/cdmoro/anki-material-notes/releases).

| Anki editor pane | File |
| --- | --- |
| Front Template | [front.html](models/front.html) |
| Back Template | [back.html](models/back.html) |
| Styling | [styles.css](models/styles.css) |

If you want these templates for a single deck, clone the note type before editing and assign the clone to those notes. Anki applies template changes to every note that uses the edited note type.

### Customize with tags

Use one variant tag per note. For example, pick one of these three green finishes.

| Finish | Example tag |
| --- | --- |
| Accent | `Material::note-green-base` |
| Filled | `Material::note-green-filled` |
| Outline | `Material::note-green-outlined` |

Replace `green` with `blue`, `purple`, `pink`, `teal`, `orange`, `indigo`, `brown`, `lime`, or `red`. Older accent tags such as `Material::note-green` still work. The neutral card also has an outlined variant (`Material::note-base-outlined`), and `Material::note-white-base` keeps the front white in either mode.

Add `Material::note-centered` separately to center the answer. Native reviewer flags and stars are styled by Anki.

### Country palettes

Use `Material::note-flag-uk` for Accent, `Material::note-flag-uk-filled` for Filled, or `Material::note-flag-uk-outlined` for Outline. The `-base` suffix also works for Accent. Each country has a thin stripe inspired by its flag and colors for light and dark mode.

Replace `uk` with `argentina`, `brazil`, `china`, `france`, `germany`, `greece`, `italy`, `japan`, `mexico`, or `usa`.

### Optional HTML inside a field

Use the field's HTML editor for accessories such as headings, labels, and cover images.

```html
<div class="text-block">
    <div class="subtitle">Related words</div>
    <span class="pill">Lunch</span>
    <span class="pill">Dinner</span>
</div>

```

For a hint, add a field such as `Pronunciation` to the note type. Put the hint text in that field and use `{{hint:Pronunciation}}` in the card template. The other examples use `{{hint:Variants}}` and `{{hint:Translation}}`.

Other classes include `header`, `subheader`, `symbol`, `emoji`, `cover`, `text-center`, `flex`, `flex-row`, `flex-col`, and `gap-sm`.

Front content aligns to the start by default. A `class="body question"` block is centered, as are front blocks marked with `center` or `text-center`. Lists align to the start inside centered blocks.

### Read-only multiple choice

Copy the templates from **Multiple choice → Source code** in the demo into a note type with the fields `Question`, `Options`, `Correct Options`, and `Explanation`. Use the same [stylesheet](models/styles.css) as the basic card.

Paste the snippets from the **Options** and **Correct Options** tabs into the corresponding fields using Anki’s HTML editor. Both fields contain the full list in the same order, using `<ol type="A">` for lettered choices. In `Correct Options`, mark correct choices with `class="correct-answer"` and incorrect choices with `class="wrong-answer"`. Incorrect choices appear struck through on the back.

## Build locally

| Command | Output |
| --- | --- |
| `make build-card` | `dist/material-notes-card.zip` with the three files for manual use |
| `make build-addon` | `dist/material-notes.ankiaddon` with the add-on and both note type templates |
| `make build-css` | Refreshes `models/styles.css` from the CSS sources in `src/styles/` |

Manual installation of the basic card requires only `front.html`, `back.html`, and `styles.css` in `models/`.

To run the demo locally, serve the repository with `python3 -m http.server 8000` and open [localhost:8000](http://localhost:8000).

The demo uses the [field horsetail photograph by H. Zell](https://commons.wikimedia.org/wiki/File:Equisetum_arvense_001.JPG) under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

## Publish a version

Set `version` in `manifest.json`, run `make build-css`, then commit and push the release changes. Tag that commit with the same version prefixed by `v`. For example, for `1.0.0`, run the following commands on the release commit.

```sh
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

On pull requests and version tags, GitHub Actions uploads `material-notes-packages` with the card files, the card ZIP, and `material-notes.ankiaddon`. A version tag also publishes a GitHub Release with the installable add-on, the three card files, and a versioned card ZIP such as `material-notes-card-v1.0.0.zip`.
