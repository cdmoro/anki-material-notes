# Material Notes for Anki

Material-style flashcards for Anki with light and dark modes. In the [interactive demo](https://anki-material-notes.netlify.app), choose a color or country palette, then choose an available finish. Use the **Show answer** icon to reveal or hide the answer. Under **Card setup**, copy the styled templates from **Front** and **Back** and use **Style → Copy style** for the CSS. The **Fields** tab lists the note fields and lets you copy each HTML example.

## Use the add-on

Open **Tools → Material Notes… → Create note type…**. Choose a template to see its purpose and the fields it will create, then choose how to apply styles.

- **Fixed style** is the default. Choose a color or country palette and select **Base**, **Filled**, or **Outlined** where available. You can also enable **Center card content**. The whole note type uses these settings and you can use tags to organize your notes.
- **Style using tags** lets you change the appearance of each note with a tag such as `Material::note-pink-outlined`. The same style applies to every card generated from that note. See [How to use style tags](docs/using-style-tags.md) for the setup and full catalog.

Leave **Note type name** blank to use the suggestion, such as `Basic - Pink Outlined` or `Basic - Tags`. If the suggested name already exists, the add-on appends `(2)`, `(3)`, and so on. Open **Add** and select the new note type to start adding notes.

**Update note types** refreshes the templates and CSS while keeping your appearance choices and the field values on existing notes. If you edited the templates or styling, the add-on asks before replacing your changes.

The managed note type list shows each type’s style and the decks containing its notes. For types styled using tags, **Change style…** can replace the style tag across all notes or notes that appear in one deck. Tags belong to notes, so cards from those notes in other decks change too. For Multiple Choice, the list shows the option count and the default shuffle, layout, labels, and feedback settings. Select a type and choose **Edit settings…** to change those defaults. Option counts can be increased; existing fields are retained.

## Copy a card into Anki

Open **Cards…** for a Basic note type with the **Front** and **Back** fields. Use the demo’s **Copy front**, **Copy back**, and **Copy style** buttons to fill the corresponding editor panes below, or copy from the files directly.

Download a versioned copy of the three files, together or individually, from [GitHub Releases](https://github.com/cdmoro/anki-material-notes/releases).

See [CHANGELOG.md](CHANGELOG.md) for the current release’s palette changes.

| Anki editor pane | File |
| --- | --- |
| Front Template | [front.html](models/front.html) |
| Back Template | [back.html](models/back.html) |
| Styling | [styles.css](models/styles.css) |

If you want these templates for a single deck, clone the note type before editing and assign the clone to those notes. Anki applies template changes to every note that uses the edited note type.

### Customize with classes or tags

For a style shared by a whole note type, choose an appearance in the add-on or add a class such as `note-green-filled` to the outer `.note` element in both templates.

The **Inverted** palette uses a black question header in light mode and a white one in dark mode. It supports Base, Filled, and Outlined finishes. Existing managed note types saved with the former White palette are updated to Inverted when their styling is refreshed.

For styling individual notes, put `{{Tags}}` in the class list of the outer `.note` element in both templates in place of any fixed palette class. The Basic templates linked above already use `{{Tags}}`. Add one palette tag per note, such as `note-green-filled` or `Material::note-green-filled`. See [How to use style tags](docs/using-style-tags.md) for step-by-step instructions and the list of colors, finishes, and country palettes.

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

Other classes include `header`, `subheader`, `symbol`, `emoji`, `cover`, `text-sm`, `text-md`, `text-base`, `text-center`, `flex`, `flex-row`, `flex-col`, and `gap-sm`. Use `text-sm` for small labels, `text-md` for explanatory copy, and `text-base` for the note’s regular text size.

Front content aligns to the start by default. A `class="body question"` block is centered, as are front blocks marked with `center` or `text-center`. Lists align to the start inside centered blocks.

### Multiple Choice — Single and Multiple

Use the add-on to create the note type, or copy [Front](models/multiple-choice-2/front.html), [Back](models/multiple-choice-2/back.html), and the shared [Styling](models/styles.css) into a note type with these fields. The add-on lets you choose between 2 and 10 answer options when creating the note type; it creates only the fields needed for that count. The default is four options.

| Field | Example |
| --- | --- |
| `Question` | Which two planets are ice giants? |
| `Option A` | Jupiter |
| `Option B` | Uranus |
| `Option C` | Saturn |
| `Option D` | Neptune |
| `Correct Answers` | `B,D` |
| `Explanation` | Uranus and Neptune are ice giants. |
| `Source` | Solar system quiz · Question 4 |

Fill in Option A and Option B. Every option after B up to the number created for the note type is optional, as are Explanation and Source. The add-on supports 2–10 options, named Option A through Option J; the website examples use four. Use tags to configure shuffle, layout, option labels, and answer feedback per note. Label tags use descriptive names such as `note-label-option-lower-roman`. The complete tag list, defaults, invalid-tag behavior, and examples are in the [Multiple Choice settings guide](docs/multiple-choice-settings.md).

In **Correct Answers**, enter letters (`A C`, `A,C`, or `A, C`) or numbers (`1 4`, `1,4`, or `1, 4`); commas and spaces can be mixed. Out-of-range options are ignored if other valid answers remain (`A, J, Z` on a four-option note keeps A). If the whole value cannot be parsed, it is treated as empty (`Cat, Dog`). Blank optional choices keep their field identities. In the add-on dialog, **Shuffle answers by default** sets the fallback for notes without a valid shuffle tag.

Choose the default answer feedback mode, feedback palette, symbols, and option layout when creating or editing the note type. Feedback palettes are **Green / red** (default), **Blue / orange**, and **Monochrome** with solid outlines for correct answers and dashed outlines for incorrect answers. **Show feedback symbols** adds ✓ and ✕ to highlighted choices on the back and is off by default. Per-note tags override those defaults. The [settings guide](docs/multiple-choice-settings.md) explains every tag value and how defaults are applied.

The demo includes **Multiple Choice — Single** and **Multiple Choice — Multiple** examples. Both use the same interactive note type: Anki shows radio buttons when `Correct Answers` identifies one choice and checkboxes when it identifies several. **Show Answer** keeps the selected choices and their order, then highlights all correct choices in green and selected incorrect choices in red by default. When shuffle is enabled by the note type default or `note-shuffle-options-2`, choices are shuffled each time. The previous order is avoided for an immediate repeat, and the current order stays the same on the back. In the demo, **Shuffle answers** also shuffles the displayed choices and reshuffles after a review rating. Each supported option count includes at least one correct choice. Use Anki’s review buttons to grade yourself.

The **Card setup** section shows the fields and lets you configure shuffle, option labels, answer feedback, feedback palette, symbols, and layout. These controls become defaults in the copied templates; tags on a note can override them later. Its template switch uses the selected palette and finish as fixed CSS classes by default; turn on **Use `{{Tags}}` instead of classes in templates** to copy templates that take their styling from note tags. See the [Multiple Choice settings guide](docs/multiple-choice-settings.md) for the full per-note tag reference.

Templates copied from the demo are standalone. Their note type defaults apply when a configuration tag is absent or invalid; add the tags above to override settings on individual notes.

The older HTML multiple-choice note type remains supported for existing collections, but is no longer offered when creating new note types.

## Build locally

| Command | Output |
| --- | --- |
| `make build-card` | `dist/material-notes-card.zip` with the three files for manual use |
| `make build-addon` | `dist/material-notes.ankiaddon` with the add-on and all note type templates |
| `make build-css` | Refreshes `models/styles.css` and the guide’s style tag catalog from the CSS sources |
| `make test` | Checks the style tag catalog and runs integration tests when Anki’s Python modules are available |

Manual installation of the basic card requires only `front.html`, `back.html`, and `styles.css` in `models/`.

To run the demo locally, serve the repository with `python3 -m http.server 8000` and open [localhost:8000](http://localhost:8000).

The demo uses the [field horsetail photograph by H. Zell](https://commons.wikimedia.org/wiki/File:Equisetum_arvense_001.JPG) under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).

## Publish a version

Set `version` in `manifest.json`, run `make build-css`, then commit and merge the release changes into `main`. A push to `main` that changes `manifest.json` builds the packages and publishes a GitHub Release tagged with the manifest version. The workflow creates that tag if needed. If you publish by pushing a version tag directly, it still checks that the tag matches the manifest.

```sh
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

On pull requests, manifest updates merged to `main`, and version tags, GitHub Actions builds the packages and uploads `material-notes-packages` with the card files, the card ZIP, and `material-notes.ankiaddon`. Manifest updates on `main` and version tags also publish a GitHub Release with the installable add-on, the three card files, and a versioned card ZIP such as `material-notes-card-v1.0.0.zip`. The demo deployment remains managed separately by Netlify.
