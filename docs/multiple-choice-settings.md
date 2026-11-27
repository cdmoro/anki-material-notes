# Multiple Choice settings with tags

Multiple Choice notes use ordinary Anki tags to set shuffle, option layout, option labels, and feedback per note. This keeps configuration out of the note’s field list. Add or remove tags in Anki’s **Tags** box; the settings apply to every card made from that note.

The templates read the tag text through `{{Tags}}` independently of the `.note` class. This is why configuration tags still work when the demo copies a template with fixed palette classes instead of `{{Tags}}` in its class list. When `{{Tags}}` is also in the class list, the script deduplicates the two sources before parsing.

## Available tags

Use at most one valid tag from each family on a note.

| Setting | Tag | Result |
| --- | --- | --- |
| Shuffle | `note-shuffle-options-1` | Keep choices in their listed order. |
| Shuffle | `note-shuffle-options-2` | Shuffle choices on each presentation. The previous order is avoided for an immediate repeat, and the current order is restored on the answer side. |
| Layout | `note-layout-1` | Show choices in one column. |
| Layout | `note-layout-2` | Show choices in two columns. |
| Option labels | `note-label-option-upper-alpha` | Letters: A, B, C… |
| Option labels | `note-label-option-decimal` | Decimal numbers: 1, 2, 3… |
| Option labels | `note-label-option-arabic-indic` | Arabic-Indic numerals: ١، ٢، ٣… |
| Option labels | `note-label-option-lower-roman` | Lowercase Roman numerals: i, ii, iii… |
| Option labels | `note-label-option-lower-greek` | Lowercase Greek letters: α, β, γ… |
| Option labels | `note-label-option-georgian` | Georgian numerals. |
| Option labels | `note-label-option-armenian` | Armenian numerals. |
| Option labels | `note-label-option-cjk-ideographic` | Chinese traditional informal numerals: 一、二、三… |
| Option labels | `note-label-option-hebrew` | Hebrew numerals. |
| Option labels | `note-label-option-japanese-informal` | Japanese informal numerals. |
| Option labels | `note-label-option-none` | No labels. |
| Answer feedback | `note-answer-feedback-1` | Correct answers and wrong selections (default for new note types). |
| Answer feedback | `note-answer-feedback-2` | All correct and incorrect options. |
| Answer feedback | `note-answer-feedback-3` | Missed correct answers and wrong selections. |
| Feedback palette | `note-feedback-palette-green-red` | Green for correct choices and red for incorrect choices. |
| Feedback palette | `note-feedback-palette-blue-orange` | Blue for correct choices and orange for incorrect choices. |
| Feedback palette | `note-feedback-palette-monochrome` | Solid outlines for correct choices and dashed outlines for incorrect choices. |
| Feedback symbols | `note-feedback-symbols-1` | Hide ✓ and ✕ (default). |
| Feedback symbols | `note-feedback-symbols-2` | Show ✓ and ✕ on highlighted choices. |

The `-1` tag is valid for shuffle, layout, answer feedback, and feedback symbols. It explicitly selects the first behavior, even when that matches the note type’s default. For example, use `note-layout-1` to force one column on a note type whose default is two columns. Option-label tags use descriptive names instead; `note-label-option-upper-alpha` explicitly selects letter labels.

New Multiple Choice note types default to no option labels. Add `note-label-option-upper-alpha` or another label tag to show labels, or change the note type’s **Option labels** default in the add-on. Existing note types keep the default already saved in their template; choose **None** in **Edit settings…** to change one to the new default.

## Answer feedback

The back keeps your selections visible with radio buttons or checkboxes. The feedback mode determines which options are highlighted. The table uses the default Green / red palette.

| Option on the back | Correct answers and wrong selections | All correct and incorrect options | Missed correct answers and wrong selections |
| --- | --- | --- | --- |
| Correct and selected | Green | Green | Neutral |
| Correct and unselected | Green | Green | Green |
| Incorrect and selected | Red | Red | Red |
| Incorrect and unselected | Neutral | Red | Neutral |

For example, if **A** and **C** are correct and you select **A** and **B**, the default mode shows **A** in green with its box checked, **B** in red with its box checked, **C** in green with its box empty, and **D** with no highlight. The same rules apply to single-answer cards.

The add-on uses this mode for new Multiple Choice note types unless you have a saved creation preference. Existing note types keep their configured feedback when you update the templates. You can change it in **Edit settings…** or override it on an individual note with a tag.

## Feedback palette and symbols

**Feedback palette** changes how the highlights look in light and dark mode. It works with all three answer feedback modes and both option layouts.

| Palette | Correct highlight | Incorrect highlight |
| --- | --- | --- |
| **Green / red** (default) | Green background | Red background |
| **Blue / orange** | Blue background | Orange background |
| **Monochrome** | Gray background with a solid outline | Gray background with a dashed outline |

Blue / orange is an alternative for people who have difficulty distinguishing red from green. Monochrome uses outline patterns to show the result in grayscale, including when symbols are off. Neutral options have no feedback outline.

**Show feedback symbols** is off by default and works with any palette. On the back, ✓ marks a highlighted correct choice and ✕ marks a highlighted incorrect choice. The radio button or checkbox still shows whether you selected that choice. Neutral choices stay unmarked. In one column the symbol sits at the end of the first line. When symbols are on, both sides keep a small space for it so revealing the answer keeps the text wrapping stable. In two columns the symbol sits opposite the selection control in the top corner, with the option content centered.

Set these defaults when creating a Multiple Choice (JS) note type or through **Tools → Material Notes… → Edit settings…**. The creation dialog remembers your last choices for future note types. To use per-note overrides on an older managed type, update its templates and styling from the add-on first. For manually copied templates, copy both sides and the stylesheet from the demo. Feedback settings work with either fixed card styling or styling by tags.

## Defaults and invalid tags

Each setting falls back independently. If its tag is missing or invalid, the note type’s configured behavior applies. Set the fallback values when creating or editing the note type in **Tools → Material Notes…**. For shuffle, this includes the note type’s default and its **Use each note’s shuffle tag**, **Always shuffle**, or **Never shuffle** policy. A valid shuffle tag overrides that policy for the individual note.

The website demo’s **Shuffle by default**, **Option labels**, **Answer feedback**, **Feedback palette**, **Show feedback symbols**, and **Option layout** controls set these fallback values in the templates it generates. They do not create configuration tags. Add tags to a note in Anki when a particular note should differ from the template defaults.

Tags must use the exact spelling and a supported value shown above. Unsupported values such as `note-layout-3` and `note-answer-feedback-234523` are ignored. If a note has multiple valid tags from one setting family, that setting falls back to the note type behavior; it does not depend on tag order. Invalid tags do not prevent valid tags from other families from applying.

The add-on reserves tags beginning with `note-shuffle-options-`, `note-layout-`, `note-label-option-`, `note-answer-feedback-`, `note-feedback-palette-`, and `note-feedback-symbols-` on Multiple Choice cards. It removes those tags from the card’s CSS classes, including malformed values, so they cannot act as palette, theme, or centering classes. Visual tags such as `note-pink-outlined` and `note-centered` continue to work alongside configuration tags. The optional `Material::` prefix is also accepted.

## Examples

| Tags on the note | Result |
| --- | --- |
| *(no configuration tags)* | Use the note type defaults. |
| `note-shuffle-options-2 note-layout-2` | Shuffle choices and show two columns; use note type defaults for labels and feedback. |
| `note-label-option-none note-answer-feedback-3` | Hide option labels and highlight missed correct answers and wrong selections. |
| `note-pink-outlined note-centered note-layout-1` | Use the pink outlined theme, center card content, and show one column. |
| `note-feedback-palette-blue-orange note-feedback-symbols-2` | Use blue and orange highlights with symbols on the back. |
| `Material::note-feedback-palette-monochrome note-feedback-symbols-1` | Use solid and dashed feedback outlines with symbols hidden. |
| `note-layout-1 note-layout-2` | Use the note type’s default layout because two valid layout tags are present. |

Tags belong to notes rather than individual cards. If one note creates forward and reverse cards, the same configuration tags affect both. For card-specific behavior, use separate notes or separate templates.

## Multiple Choice fields

The configuration tags replace the `Shuffle Options` and `Option Layout` fields. The content fields remain:

- `Question`
- `Option A` and `Option B` (required), plus any additional options up to `Option J`
- `Correct Answers` (required to color answers correctly)
- `Explanation` and `Source` (optional)

In **Correct Answers**, enter letters (`A C` or `A,C`) or option numbers (`1 3`), separated by spaces, commas, or both. Number 1 means Option A. Blank optional choices keep their positions and labels when choices are shuffled.
