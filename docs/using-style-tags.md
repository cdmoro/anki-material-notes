# Using style tags

Style tags are ordinary Anki tags that Material Notes uses to set a note’s color and finish. A single note type can have a pink outlined note and a blue filled note. The finish controls how the color is used. **Base** uses the palette as an accent, **Filled** tints the card, and **Outlined** gives the card a border.

## Choose how to apply styles

| Style application | Where to set the appearance | What it applies to |
| --- | --- | --- |
| **Fixed style** (default) | Choose a palette and finish when creating the note type. | Every note of that type uses those same settings. Tags can still organize your notes. |
| **Style using tags** | Add a style tag to each note. | Notes of the same type can have different styles. All cards from one note share its tags. |

## Set up the note type

### With the add-on

1. In Anki Desktop, open **Tools → Material Notes… → Create note type…**.
2. Choose a template, then select **Style using tags** under **Style application**.
3. Enter a name or leave it blank to use the suggestion, such as `Basic - Tags`. Select **Create**.
4. Open **Add** and select your new note type.

### With manually installed templates

In Anki Desktop, open **Cards…** for your note type and paste the Material Notes [stylesheet](../models/styles.css) into **Styling**. Put `{{Tags}}` in the class list of the outer `.note` element on the front and back. If you copied a fixed-style template from the demo, replace its palette and finish class with `{{Tags}}` and keep the template’s structural classes.

```html
<!-- Front Template outer element -->
<div class="note front {{Tags}}">

<!-- Back Template outer element -->
<div class="note back {{Tags}}">
```

The repository’s [Basic front](../models/front.html) and [Basic back](../models/back.html) already include `{{Tags}}`. For a fixed manual style, replace `{{Tags}}` with a class such as `note-pink-outlined` on both sides.

## Add, change, or remove a style

1. When adding a note, paste `Material::note-pink-outlined` into **Tags**. Keep any tags you use for organization, such as `language::italian`.
2. To change the style, open **Browse**, select the note or one of its cards, and edit **Tags** in the editor. Remove `Material::note-pink-outlined` and add `note-blue-filled`. All cards generated from that note now use the blue filled style.
3. To return to the default appearance, remove the palette tag from **Tags**. The default palette and Base finish apply when there is no palette tag.

For an add-on note type configured with **Style using tags**, select it in **Tools → Material Notes…** and choose **Change style…** to replace the style tag for all its notes or for notes with cards in one deck. The add-on keeps other tags. Since tags belong to notes, all cards from a selected note change style, including cards in other decks; the add-on explains this before applying the change.

Use the spellings below as shown. Each tag can be entered as written or with the `Material::` prefix. For example, `note-green-base` and `Material::note-green-base` produce the same appearance. The prefix groups the tags under **Material** in Anki.

Use **one palette and finish tag per note**. If several match, the CSS cascade resolves each property according to the stylesheet’s rule order. Reordering tags in Anki has no effect. Mixing styles can combine properties, for example a filled background and an outline. The optional `note-centered` or `Material::note-centered` tag centers card content and can be used alongside a palette tag. Multiple Choice also reserves `note-shuffle-options-*`, `note-layout-*`, `note-label-option-*`, `note-answer-feedback-*`, `note-feedback-palette-*`, and `note-feedback-symbols-*` tags for per-note configuration. The template removes those reserved tags from its CSS classes, so they can coexist with palette and centered tags. Keep other organizational tags distinct from template class names such as `front` and `back`.

For the full Multiple Choice configuration tag list and examples, see the [Multiple Choice settings guide](multiple-choice-settings.md).

Tags belong to the note, so style tags affect all cards generated from it, including forward and reverse cards. To give sibling cards different appearances, use card-specific templates with their own fixed classes. See the [Anki Manual on tags](https://docs.ankiweb.net/editing.html#using-tags).

## Available palette tags

The Base aliases produce the same result as the corresponding Base tags. A dash indicates an unavailable tag. The default Base appearance applies with no palette tag. Country palettes add a flag-inspired stripe to the front. Inverted uses a black question header in light mode and a white question header in dark mode; all three finishes are available.

<!-- BEGIN STYLE TAG CATALOG -->

| Palette | Base | Filled | Outlined | Base alias |
| --- | --- | --- | --- | --- |
| Default | — | `note-base-filled` | `note-base-outlined` | — |
| Blue | `note-blue-base` | `note-blue-filled` | `note-blue-outlined` | `note-blue` |
| Brown | `note-brown-base` | `note-brown-filled` | `note-brown-outlined` | `note-brown` |
| Green | `note-green-base` | `note-green-filled` | `note-green-outlined` | `note-green` |
| Indigo | `note-indigo-base` | `note-indigo-filled` | `note-indigo-outlined` | `note-indigo` |
| Inverted | `note-inverted-base` | `note-inverted-filled` | `note-inverted-outlined` | `note-inverted` |
| Lime | `note-lime-base` | `note-lime-filled` | `note-lime-outlined` | `note-lime` |
| Orange | `note-orange-base` | `note-orange-filled` | `note-orange-outlined` | `note-orange` |
| Pink | `note-pink-base` | `note-pink-filled` | `note-pink-outlined` | `note-pink` |
| Purple | `note-purple-base` | `note-purple-filled` | `note-purple-outlined` | `note-purple` |
| Red | `note-red-base` | `note-red-filled` | `note-red-outlined` | `note-red` |
| Teal | `note-teal-base` | `note-teal-filled` | `note-teal-outlined` | `note-teal` |
| Argentina | `note-flag-argentina-base` | `note-flag-argentina-filled` | `note-flag-argentina-outlined` | `note-flag-argentina` |
| Brazil | `note-flag-brazil-base` | `note-flag-brazil-filled` | `note-flag-brazil-outlined` | `note-flag-brazil` |
| China | `note-flag-china-base` | `note-flag-china-filled` | `note-flag-china-outlined` | `note-flag-china` |
| France | `note-flag-france-base` | `note-flag-france-filled` | `note-flag-france-outlined` | `note-flag-france` |
| Germany | `note-flag-germany-base` | `note-flag-germany-filled` | `note-flag-germany-outlined` | `note-flag-germany` |
| Greece | `note-flag-greece-base` | `note-flag-greece-filled` | `note-flag-greece-outlined` | `note-flag-greece` |
| Italy | `note-flag-italy-base` | `note-flag-italy-filled` | `note-flag-italy-outlined` | `note-flag-italy` |
| Japan | `note-flag-japan-base` | `note-flag-japan-filled` | `note-flag-japan-outlined` | `note-flag-japan` |
| Mexico | `note-flag-mexico-base` | `note-flag-mexico-filled` | `note-flag-mexico-outlined` | `note-flag-mexico` |
| United Kingdom | `note-flag-uk-base` | `note-flag-uk-filled` | `note-flag-uk-outlined` | `note-flag-uk` |
| USA | `note-flag-usa-base` | `note-flag-usa-filled` | `note-flag-usa-outlined` | `note-flag-usa` |

<!-- END STYLE TAG CATALOG -->
