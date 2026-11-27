import ast
import re
import runpy
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.build_css import GUIDE, ROOT, render_card_setup_sources, style_tags, update_guide_catalog

try:
    from anki.collection import Collection
    from aqt.qt import QApplication
except ModuleNotFoundError:
    Collection = None


class StyleCatalogTests(unittest.TestCase):
    def test_catalog_is_current(self):
        css = (ROOT / "models" / "styles.css").read_text(encoding="utf-8")
        guide = GUIDE.read_text(encoding="utf-8")
        self.assertEqual(guide, update_guide_catalog(guide, css))
        self.assertIn("note-centered", style_tags(css))
        self.assertIn("note-flag-uk-filled", style_tags(css))
        self.assertNotIn("note-white-base", style_tags(css))

    def test_inverted_palette_parity_across_addon_demo_and_css(self):
        addon_path = ROOT / "__init__.py"
        addon_tree = ast.parse(addon_path.read_text(encoding="utf-8"))
        assignments = {
            target.id: node.value
            for node in addon_tree.body if isinstance(node, ast.Assign)
            for target in node.targets if isinstance(target, ast.Name)
        }
        colors = ast.literal_eval(assignments["COLORS"])
        finishes = ast.literal_eval(assignments["FINISHES"])
        finish_function = next(
            node for node in addon_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "available_finishes"
        )
        normalize_function = next(
            node for node in addon_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "normalize_appearance"
        )
        namespace = {"FINISHES": finishes}
        exec(compile(ast.Module(body=[finish_function, normalize_function], type_ignores=[]), str(addon_path), "exec"), namespace)

        html = (ROOT / "index.html").read_text(encoding="utf-8")
        palette_select = re.search(r'<select id="color"[\s\S]*?</select>', html).group(0)
        demo_palettes = dict(re.findall(r'<option value="([^"]+)">([^<]+)</option>', palette_select))
        main_js = (ROOT / "src" / "js" / "main.js").read_text(encoding="utf-8")
        finish_picker = re.search(r"function availableFinishes\(color\)\s*\{([^}]+)\}", main_js).group(1)
        css = (ROOT / "models" / "styles.css").read_text(encoding="utf-8")
        tags = style_tags(css)

        self.assertIn("Inverted", colors)
        self.assertEqual(demo_palettes.get("inverted"), "Inverted")
        self.assertNotIn("white", demo_palettes)
        self.assertIn('["base", "filled", "outlined"]', finish_picker)
        self.assertEqual(namespace["available_finishes"]("inverted"), tuple(finishes))
        self.assertEqual(tuple(finishes), ("base", "filled", "outlined"))
        self.assertEqual(namespace["normalize_appearance"]({"palette": "white", "finish": "filled"}), {
            "palette": "inverted", "finish": "filled",
        })
        for style_tag in (
            "note-inverted", "note-inverted-base",
            "note-inverted-filled", "note-inverted-outlined",
        ):
            self.assertIn(style_tag, tags)
        self.assertNotIn("note-white-base", tags)
        elements_css = (ROOT / "src" / "styles" / "elements.css").read_text(encoding="utf-8")
        for style_tag in (
            "note-inverted", "note-inverted-base",
            "note-inverted-filled", "note-inverted-outlined",
        ):
            self.assertIn(f".note.front:is(.{style_tag}, .Material\\:\\:{style_tag}) .question-options", elements_css)
        self.assertIn("color-mix(in srgb, var(--font-color) 22%, var(--surface));", elements_css)
        variant_css = (ROOT / "src" / "styles" / "variants.css").read_text(encoding="utf-8")
        inverted_css = re.search(
            r"\.note:is\(\.note-inverted, \.Material\\:\\:note-inverted\),[\s\S]*?\n\}",
            variant_css,
        ).group(0)
        self.assertIn("--palette-light: #000", inverted_css)
        self.assertIn("--palette-dark: #fff", inverted_css)
        self.assertIn("--ink-light: #fff", inverted_css)
        self.assertIn("--ink-dark: #000", inverted_css)
        self.assertIn("background: var(--palette-front)", variant_css)
        self.assertIn("color: var(--palette-ink)", variant_css)
        self.assertRegex(variant_css, r"(?s)\.note:is\(\.note-inverted-filled, \.Material\\:\\:note-inverted-filled\),.*?--note-background: var\(--palette-fill\);")
        self.assertRegex(variant_css, r"(?s)\.note:is\(\.note-inverted-outlined, \.Material\\:\\:note-inverted-outlined\),.*?--note-border: 2px solid var\(--outline\);")

    def test_card_setup_sources_are_current(self):
        css = (ROOT / "models" / "styles.css").read_text(encoding="utf-8")
        sources = (ROOT / "src" / "js" / "card-setup-sources.js").read_text(encoding="utf-8")
        self.assertEqual(sources, render_card_setup_sources(css))


@unittest.skipIf(Collection is None, "Anki's Python modules are required")
class AnkiStyleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.addon = runpy.run_path(str(ROOT / "__init__.py"))

    def setUp(self):
        directory = TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.collection = Collection(str(Path(directory.name) / "test.anki2"))
        self.addCleanup(self.collection.close)
        self.models = self.collection.models

    def test_fixed_and_tag_templates_for_every_preset(self):
        css = (ROOT / "models" / "styles.css").read_text(encoding="utf-8")
        tags = style_tags(css)
        for example in self.addon["STYLE_TAG_EXAMPLES"]:
            self.assertIn(example.removeprefix("Material::"), tags)
        for palette in self.addon["PALETTE_NAMES"]:
            for finish in self.addon["available_finishes"](palette):
                self.assertLessEqual(set(self.addon["appearance_classes"](palette, finish)), tags)

        appearance = {"palette": "pink", "finish": "outlined", "centered": True}
        for kind, preset in self.addon["NOTE_TYPES"].items():
            for mode, expected in (("fixed", "note-pink-outlined note-centered"), ("tags", "{{Tags}}")):
                with self.subTest(kind=kind, mode=mode):
                    templates = self.addon["template_content"](preset, appearance, mode)
                    for template in templates.values():
                        self.assertRegex(template, rf'<div class="[^"]* {re.escape(expected)}"(?:\s|>)')
                        config_tags = int(kind == "multiple-choice-2")
                        self.assertEqual(template.count("{{Tags}}"), int(mode == "tags") + config_tags)

    def test_note_type_names(self):
        suggest = self.addon["suggest_note_type_name"]
        self.assertEqual(suggest(self.models, "basic", "fixed", "pink", "outlined"), "Basic - Pink Outlined")
        self.assertEqual(suggest(self.models, "basic", "fixed", "blue", "filled"), "Basic - Blue Filled")
        self.assertEqual(
            suggest(self.models, "multiple-choice", "fixed", "green", "base"),
            "Multiple Choice (HTML) - Green Base",
        )
        for expected in ("Basic - Tags", "Basic - Tags (2)", "Basic - Tags (3)"):
            name = suggest(self.models, "basic", "tags", "pink", "outlined")
            self.assertEqual(name, expected)
            self.addon["create_note_type"](self.models, "basic", name, style_application="tags")

    def test_multiple_choice_uses_tags_for_card_configuration(self):
        create = self.addon["create_note_type"]
        update = self.addon["update_note_type"]
        css = (ROOT / "models" / "styles.css").read_text(encoding="utf-8")
        create(self.models, "multiple-choice-2", "Multiple Choice")
        model = self.models.byName("Multiple Choice")
        field_descriptions = {field["name"]: field.get("description", "") for field in model["flds"]}
        self.assertIn("A or A,C", field_descriptions["Correct Answers"])
        self.assertNotIn("Shuffle Options", field_descriptions)
        self.assertNotIn("Option Layout", field_descriptions)
        self.assertIn('validChoice("shuffle-options", 2)', model["tmpls"][0]["qfmt"])
        self.assertIn('validChoice("layout", 2)', model["tmpls"][0]["qfmt"])
        self.assertIn("note-label-option-", model["tmpls"][0]["qfmt"])
        self.assertIn("note-answer-feedback", model["tmpls"][0]["afmt"])
        self.assertIn('const tagsRaw = "{{Tags}}";', model["tmpls"][0]["qfmt"])
        self.assertIn('const tagsRaw = "{{Tags}}";', model["tmpls"][0]["afmt"])

        # A pre-existing managed note type gains help text on update.
        for field in model["flds"]:
            field["description"] = ""
        self.models.save(model)
        model = self.models.byName("Multiple Choice")
        self.assertEqual(update(self.models, model, css, lambda _: True), "updated")
        model = self.models.byName("Multiple Choice")
        self.assertIn("A or A,C", next(f["description"] for f in model["flds"] if f["name"] == "Correct Answers"))

        # User-authored descriptions are left intact.
        correct = next(f for f in model["flds"] if f["name"] == "Correct Answers")
        correct["description"] = "My custom hint"
        self.models.save(model)
        model = self.models.byName("Multiple Choice")
        self.assertEqual(update(self.models, model, css, lambda _: True), "up to date")
        self.assertEqual(
            next(f["description"] for f in self.models.byName("Multiple Choice")["flds"] if f["name"] == "Correct Answers"),
            "My custom hint",
        )

    def test_multiple_choice_feedback_preferences_are_saved_in_both_templates(self):
        name = "Multiple Choice"
        self.addon["create_note_type"](self.models, "multiple-choice-2", name)
        model = self.models.byName(name)
        self.assertEqual(model["mfc_feedback_palette"], "green-red")
        self.assertIs(model["mfc_feedback_symbols"], False)
        self.assertIn('const defaultFeedbackPalette = "green-red";', model["tmpls"][0]["afmt"])
        self.assertIn("const defaultFeedbackSymbols = false;", model["tmpls"][0]["qfmt"])

        model["css"] = "/* Previously installed stylesheet */"
        self.addon["record_installed_content"](model, "multiple-choice-2", model["css"], model["tmpls"][0])
        self.models.save(model)
        result = self.addon["edit_note_type_settings"](
            self.models, model, None, "fixed", False, 4, "correct-and-errors", "field",
            "none", 2, lambda _: False, feedback_palette="blue-orange", feedback_symbols=True,
        )
        self.assertEqual(result, "updated")
        model = self.models.byName(name)
        self.assertEqual(model["mfc_feedback_palette"], "blue-orange")
        self.assertIs(model["mfc_feedback_symbols"], True)
        self.assertIn(".mc2-show-feedback-symbols", model["css"])

        css = model["css"] + "\n/* Updated styling */"
        self.assertEqual(self.addon["update_note_type"](self.models, model, css, lambda _: False), "updated")
        template = self.models.byName(name)["tmpls"][0]
        self.assertIn('const defaultFeedbackPalette = "blue-orange";', template["afmt"])
        self.assertIn("const defaultFeedbackSymbols = true;", template["qfmt"])

    def test_anki_renders_and_updates_all_style_modes(self):
        appearance = {"palette": "pink", "finish": "outlined"}
        for mode, expected_class in (
            ("fixed", "note-pink-outlined"),
            ("tags", "Material::note-blue-filled"),
            ("legacy", "note-pink-outlined Material::note-blue-filled"),
        ):
            with self.subTest(mode=mode):
                initial_mode = "fixed" if mode == "legacy" else mode
                self.addon["create_note_type"](self.models, "basic", mode, appearance, initial_mode)
                model = self.models.byName(mode)
                if mode == "legacy":
                    del model["mfc_style_application"]
                    template = model["tmpls"][0]
                    preset = self.addon["NOTE_TYPES"]["basic"]
                    template.update(self.addon["template_content"](preset, appearance, "legacy"))
                    self.addon["record_installed_content"](model, "basic", model["css"], template)
                    self.models.save(model)
                old_template = model["tmpls"][0].copy()
                note = self.collection.new_note(model)
                note["Front"], note["Back"] = "Question", "Answer"
                note.tags = ["Material::note-blue-filled", "subject::science"]
                self.collection.add_note(note, 1)
                card = note.cards()[0]
                for side in (card.question(), card.answer()):
                    self.assertIn(expected_class, side)
                    self.assertEqual("subject::science" in side, mode != "fixed")
                updated_css = model["css"] + "\n/* Updated style */"
                update = self.addon["update_note_type"]
                self.assertEqual(update(self.models, model, updated_css, lambda _: False), "updated")
                self.assertEqual(self.models.byName(mode)["tmpls"][0], old_template)
                self.assertEqual(self.collection.get_note(note.id)["Back"], "Answer")

    def test_dialog_placeholder_and_create_follow_selected_mode(self):
        app = QApplication.instance() or QApplication([])
        dialog = self.addon["CreateNoteTypeDialog"](None, self.models)
        self.assertEqual(dialog.name.placeholderText(), "Basic - Default Base")
        dialog.palette.setCurrentIndex(dialog.palette.findData("inverted"))
        self.assertEqual(dialog.name.placeholderText(), "Basic - Inverted Base")
        self.assertEqual(dialog.finish.count(), 3)
        dialog.style_application.setCurrentIndex(dialog.style_application.findData("tags"))
        self.assertTrue(dialog.fixed_controls.isHidden())
        self.assertFalse(dialog.tag_controls.isHidden())
        self.assertEqual(dialog.name.placeholderText(), "Basic - Tags")
        dialog.copy_style_tag()
        self.assertEqual(app.clipboard().text(), dialog.tag_examples.currentText())
        dialog.create()
        self.assertEqual(self.models.byName("Basic - Tags")["mfc_style_application"], "tags")

    def test_tags_can_be_replaced_and_removed_on_the_same_note(self):
        self.addon["create_note_type"](self.models, "basic", "Basic - Tags", style_application="tags")
        note = self.collection.new_note(self.models.byName("Basic - Tags"))
        note["Front"], note["Back"] = "Question", "Answer"
        note.tags = ["note-pink-outlined", "subject::science"]
        self.collection.add_note(note, 1)
        card_id = note.cards()[0].id

        for tag in ("Material::note-blue-filled", None):
            note.tags = ["subject::science", tag] if tag else ["subject::science"]
            self.collection.update_note(note)
            card = self.collection.get_card(card_id)
            for side in (card.question(), card.answer()):
                self.assertNotIn("note-pink-outlined", side.split("</style>")[-1])
                self.assertIn("subject::science", side)
                self.assertEqual("Material::note-blue-filled" in side, tag is not None)
