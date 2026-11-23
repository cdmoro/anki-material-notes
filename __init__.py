"""Manage Material Notes note types in the active Anki collection."""

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path

from anki.consts import MODEL_STD
from anki.errors import AnkiError
from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QSettings,
    QSpinBox,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import askUser, showInfo

MODEL_DIR = Path(__file__).resolve().parent / "models"
ADDON_CONFIG_KEY = "shuffle_answers_by_default"
NOTE_TYPES = json.loads((MODEL_DIR / "presets.json").read_text(encoding="utf-8"))
GUIDE_URL = "https://github.com/cdmoro/anki-material-notes/blob/main/docs/using-style-tags.md"
STYLE_TAG_EXAMPLES = (
    "note-pink-outlined",
    "Material::note-blue-filled",
    "Material::note-flag-uk",
)
COLORS = (
    "White", "Blue", "Purple", "Pink", "Teal", "Green",
    "Orange", "Indigo", "Brown", "Lime", "Red",
)
COUNTRIES = (
    ("Argentina", "ar", "argentina"), ("Brazil", "br", "brazil"),
    ("China", "cn", "china"), ("France", "fr", "france"),
    ("Germany", "de", "germany"), ("Greece", "gr", "greece"),
    ("Italy", "it", "italy"), ("Japan", "jp", "japan"),
    ("Mexico", "mx", "mexico"), ("United Kingdom", "gb", "uk"),
    ("USA", "us", "usa"),
)
PALETTE_NAMES = {
    "base": "Default",
    **{color.lower(): color for color in COLORS},
    **{f"flag-{slug}": country for country, _, slug in COUNTRIES},
}
FINISHES = {"base": "Base", "filled": "Filled", "outlined": "Outlined"}
MULTIPLE_CHOICE_KIND = "multiple-choice-2"
MULTIPLE_CHOICE_DEFAULT_COUNT = 4
MULTIPLE_CHOICE_MAX_COUNT = 10
ANSWER_COLORING_CONFIG_KEY = "answer_coloring_by_default"
ANSWER_COLORING_ALL = "all"
ANSWER_COLORING_MISTAKES = "mistakes"
SHUFFLE_POLICY_FIELD = "field"
SHUFFLE_POLICY_ALWAYS = "always"
SHUFFLE_POLICY_NEVER = "never"
SHUFFLE_POLICIES = {SHUFFLE_POLICY_FIELD, SHUFFLE_POLICY_ALWAYS, SHUFFLE_POLICY_NEVER}
OPTION_LABELS_LETTERS = "letters"
OPTION_LABELS_NUMBERS = "numbers"
OPTION_LABELS_NONE = "none"
OPTION_LABELS = {OPTION_LABELS_LETTERS, OPTION_LABELS_NUMBERS, OPTION_LABELS_NONE}


def read_model_file(path):
    return path.read_text(encoding="utf-8")


def configured_answer_coloring():
    value = QSettings("Material Notes", "Material Notes").value(
        ANSWER_COLORING_CONFIG_KEY, ANSWER_COLORING_ALL, type=str
    )
    return value if value in {ANSWER_COLORING_ALL, ANSWER_COLORING_MISTAKES} else ANSWER_COLORING_ALL


def css_version(css):
    header, end, _ = css.lstrip().partition("*/")
    if not end or not header.startswith("/*"):
        return None

    version = re.search(
        r"(?:^\s*\*\s*Version:[ \t]*|·[ \t]*)"
        r"(\d+\.\d+\.\d+(?:-[\w.-]+)?(?:\+[\w.-]+)?)[ \t]*\r?$",
        header,
        re.MULTILINE,
    )
    return version.group(1) if version else None


def available_finishes(palette):
    if palette == "white":
        return ("base",)
    return tuple(FINISHES)


def appearance_classes(palette="base", finish="base", centered=False):
    classes = []
    if palette != "base" or finish != "base":
        suffix = "" if palette.startswith("flag-") and finish == "base" else f"-{finish}"
        classes.append(f"note-{palette}{suffix}")
    if centered:
        classes.append("note-centered")
    return classes


def multiple_choice_option_count(model=None, requested=None, default=MULTIPLE_CHOICE_DEFAULT_COUNT):
    if requested is not None:
        return max(2, min(MULTIPLE_CHOICE_MAX_COUNT, int(requested)))
    if model and model.get("mfc_option_count"):
        return max(2, min(MULTIPLE_CHOICE_MAX_COUNT, int(model["mfc_option_count"])))
    if model:
        option_fields = {
            field["name"] for field in model["flds"]
            if re.fullmatch(r"Option [A-J]", field["name"])
        }
        if option_fields:
            return max(ord(name[-1]) - ord("A") + 1 for name in option_fields)
    return default


def preset_fields(kind, preset=None, option_count=None):
    preset = preset or NOTE_TYPES[kind]
    if kind != MULTIPLE_CHOICE_KIND:
        return list(preset["fields"])
    count = multiple_choice_option_count(
        requested=option_count, default=preset.get("option_count_default", MULTIPLE_CHOICE_DEFAULT_COUNT)
    )
    options = [f"Option {chr(ord('A') + index)}" for index in range(count)]
    return ["Question", *options, "Correct Answers", "Shuffle Options", "Explanation", "Source"]


def template_content(
    preset, appearance=None, style_application="fixed", shuffle_default=False, option_count=None,
    answer_coloring=ANSWER_COLORING_ALL, shuffle_policy=SHUFFLE_POLICY_FIELD,
    option_labels=OPTION_LABELS_LETTERS,
):
    classes = [] if style_application == "tags" else appearance_classes(**(appearance or {}))
    if style_application != "fixed":
        classes.append("{{Tags}}")
    replacement = " " + " ".join(classes) if classes else ""
    templates = {
        key: read_model_file(MODEL_DIR / preset[side]).replace(" {{Tags}}", replacement, 1)
        .replace("const defaults = false;", f"const defaults = {str(bool(shuffle_default)).lower()};")
        .replace('const answerColoring = "all";', f'const answerColoring = "{answer_coloring}";')
        .replace('const shufflePolicy = "field";', f'const shufflePolicy = "{shuffle_policy}";')
        .replace('const optionLabels = "letters";', f'const optionLabels = "{option_labels}";')
        for key, side in (("qfmt", "front"), ("afmt", "back"))
    }
    if preset.get("front") == "multiple-choice-2/front.html":
        count = multiple_choice_option_count(
            requested=option_count, default=preset.get("option_count_default", MULTIPLE_CHOICE_DEFAULT_COUNT)
        )
        for letter in "CDEFGHIJ"[max(0, count - 2):]:
            block = re.escape(f"{{{{#Option {letter}}}}}") + ".*?" + re.escape(f"{{{{/Option {letter}}}}}")
            templates["qfmt"] = re.sub(
                block, "", templates["qfmt"], flags=re.DOTALL,
            )
    return templates


def suggest_note_type_name(models, kind, style_application, palette, finish):
    label = NOTE_TYPES[kind]["label"]
    style = "Tags" if style_application == "tags" else f"{PALETTE_NAMES[palette]} {FINISHES[finish]}"
    base_name = f"{label} - {style}"
    name = base_name
    suffix = 2
    while models.byName(name):
        name = f"{base_name} ({suffix})"
        suffix += 1
    return name


def content_hash(*parts):
    return hashlib.sha1("\0".join(parts).encode("utf-8")).hexdigest()


def record_installed_content(model, kind, css, template):
    model["mfc_managed_by_addon"] = True
    model["mfc_kind"] = kind
    model["mfc_original_css_hash"] = content_hash(css)
    model["mfc_template_hash"] = content_hash(template["qfmt"], template["afmt"])


def create_note_type(
    models, kind, name, appearance=None, style_application="fixed", shuffle_default=False,
    option_count=None, answer_coloring=ANSWER_COLORING_ALL,
    shuffle_policy=SHUFFLE_POLICY_FIELD, option_labels=OPTION_LABELS_LETTERS,
):
    preset = NOTE_TYPES[kind]
    if answer_coloring not in {ANSWER_COLORING_ALL, ANSWER_COLORING_MISTAKES}:
        answer_coloring = ANSWER_COLORING_ALL
    if shuffle_policy not in SHUFFLE_POLICIES:
        shuffle_policy = SHUFFLE_POLICY_FIELD
    if option_labels not in OPTION_LABELS:
        option_labels = OPTION_LABELS_LETTERS
    model = models.new(name)
    count = multiple_choice_option_count(
        requested=option_count, default=preset.get("option_count_default", MULTIPLE_CHOICE_DEFAULT_COUNT)
    ) if kind == MULTIPLE_CHOICE_KIND else None
    descriptions = preset.get("field_descriptions", {})
    for field_name in preset_fields(kind, preset, count):
        field = models.newField(field_name)
        field["description"] = descriptions.get(field_name, "")
        models.addField(model, field)

    css = read_model_file(MODEL_DIR / "styles.css")
    template = models.newTemplate("Card 1")
    template.update(template_content(
        preset, appearance, style_application, shuffle_default, count, answer_coloring,
        shuffle_policy, option_labels,
    ))
    models.addTemplate(model, template)
    model["css"] = css
    model["mfc_style_application"] = style_application
    model["mfc_shuffle_default"] = bool(shuffle_default)
    if count is not None:
        model["mfc_option_count"] = count
        model["mfc_answer_coloring"] = answer_coloring
        model["mfc_shuffle_policy"] = shuffle_policy
        model["mfc_option_labels"] = option_labels
    if appearance and style_application == "fixed":
        model["mfc_appearance"] = appearance
    record_installed_content(model, kind, css, template)
    models.add(model)


def managed_note_types(models):
    return sorted(
        (model for model in models.all() if model.get("mfc_managed_by_addon")),
        key=lambda model: model["name"].casefold(),
    )


def update_note_type(models, model, css, confirm_overwrite):
    kind = model.get("mfc_kind", "basic")
    if kind not in NOTE_TYPES or model["type"] != MODEL_STD:
        return "incompatible"

    preset = NOTE_TYPES[kind]
    option_count = multiple_choice_option_count(
        model, default=preset.get("option_count_default", MULTIPLE_CHOICE_DEFAULT_COUNT)
    ) if kind == MULTIPLE_CHOICE_KIND else None
    required_fields = preset_fields(kind, preset, option_count)
    missing_fields = set(required_fields) - {field["name"] for field in model["flds"]}
    if kind == "multiple-choice-2" and missing_fields == {"Shuffle Options"}:
        updated = deepcopy(model)
        models.addField(updated, models.newField("Shuffle Options"))
        models.save(updated)
        model = models.byName(model["name"])
    model_fields = {field["name"] for field in model["flds"]}
    if not model_fields.issuperset(required_fields) or len(model["tmpls"]) != 1:
        return "incompatible"

    # Fill in descriptions for addon-managed fields without replacing text the
    # user may have entered in Anki's field settings.
    descriptions = preset.get("field_descriptions", {})
    fields_changed = False
    updated = deepcopy(model)
    for field in updated["flds"]:
        description = descriptions.get(field["name"])
        if description and not field.get("description"):
            field["description"] = description
            fields_changed = True

    installed = model["tmpls"][0]
    answer_coloring = model.get("mfc_answer_coloring", ANSWER_COLORING_ALL)
    if answer_coloring not in {ANSWER_COLORING_ALL, ANSWER_COLORING_MISTAKES}:
        answer_coloring = ANSWER_COLORING_ALL
    shuffle_policy = model.get("mfc_shuffle_policy", SHUFFLE_POLICY_FIELD)
    if shuffle_policy not in SHUFFLE_POLICIES:
        shuffle_policy = SHUFFLE_POLICY_FIELD
    option_labels = model.get("mfc_option_labels", OPTION_LABELS_LETTERS)
    if option_labels not in OPTION_LABELS:
        option_labels = OPTION_LABELS_LETTERS
    latest = template_content(
        preset, model.get("mfc_appearance"), model.get("mfc_style_application", "legacy"),
        model.get("mfc_shuffle_default", False), option_count,
        answer_coloring, shuffle_policy, option_labels,
    )
    css_changed = css != model["css"]
    template_changed = any(installed[key] != value for key, value in latest.items())
    if not css_changed and not template_changed:
        if fields_changed:
            models.save(updated)
            return "updated"
        return "up to date"

    custom_css = css_changed and model.get("mfc_original_css_hash") != content_hash(model["css"])
    custom_template = template_changed and model.get("mfc_template_hash") != content_hash(
        installed["qfmt"], installed["afmt"]
    )
    if (custom_css or custom_template) and not confirm_overwrite(model["name"]):
        return "skipped"

    updated["css"] = css
    updated["tmpls"][0].update(latest)
    if option_count is not None:
        updated["mfc_option_count"] = option_count
        updated["mfc_answer_coloring"] = answer_coloring
        updated["mfc_shuffle_policy"] = shuffle_policy
        updated["mfc_option_labels"] = option_labels
    record_installed_content(updated, kind, css, latest)
    models.save(updated)
    return "updated"


def edit_note_type_settings(
    models, model, appearance, style_application, shuffle_default, option_count,
    answer_coloring, shuffle_policy, option_labels, confirm_overwrite,
):
    kind = model.get("mfc_kind", "basic")
    if kind not in NOTE_TYPES or model["type"] != MODEL_STD:
        return "incompatible"

    preset = NOTE_TYPES[kind]
    is_multiple_choice = kind == MULTIPLE_CHOICE_KIND
    if answer_coloring not in {ANSWER_COLORING_ALL, ANSWER_COLORING_MISTAKES}:
        answer_coloring = ANSWER_COLORING_ALL
    if shuffle_policy not in SHUFFLE_POLICIES:
        shuffle_policy = SHUFFLE_POLICY_FIELD
    if option_labels not in OPTION_LABELS:
        option_labels = OPTION_LABELS_LETTERS

    updated = deepcopy(model)
    current_count = multiple_choice_option_count(
        model, default=preset.get("option_count_default", MULTIPLE_CHOICE_DEFAULT_COUNT)
    ) if is_multiple_choice else None
    if is_multiple_choice:
        option_count = max(current_count, min(MULTIPLE_CHOICE_MAX_COUNT, int(option_count)))
        for index in range(current_count, option_count):
            field = models.newField(f"Option {chr(ord('A') + index)}")
            models.addField(updated, field)

    updated["mfc_style_application"] = style_application
    if style_application == "fixed":
        updated["mfc_appearance"] = appearance or {}
    updated["mfc_shuffle_default"] = bool(shuffle_default)
    if is_multiple_choice:
        updated["mfc_option_count"] = option_count
        updated["mfc_answer_coloring"] = answer_coloring
        updated["mfc_shuffle_policy"] = shuffle_policy
        updated["mfc_option_labels"] = option_labels

    latest = template_content(
        {**preset, "kind": kind}, updated.get("mfc_appearance"), style_application,
        shuffle_default, option_count, answer_coloring, shuffle_policy, option_labels,
    )
    installed = model["tmpls"][0]
    template_changed = any(installed[key] != value for key, value in latest.items())
    custom_template = model.get("mfc_template_hash") != content_hash(
        installed["qfmt"], installed["afmt"]
    )
    if template_changed and custom_template and not confirm_overwrite(model["name"]):
        return "skipped"

    updated["tmpls"][0].update(latest)
    record_installed_content(updated, kind, updated["css"], latest)
    models.save(updated)
    return "updated"


class CreateNoteTypeDialog(QDialog):
    def __init__(self, parent, models):
        super().__init__(parent)
        self.models = models
        self.setWindowTitle("Create Material note type")
        self.setMinimumWidth(520)

        self.kind = QComboBox()
        for kind, preset in NOTE_TYPES.items():
            if not preset.get("deprecated"):
                self.kind.addItem(preset["label"], kind)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setMinimumHeight(44)
        self.name = QLineEdit()
        self.fields = QLabel()
        self.fields.setWordWrap(True)
        self.fields.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.option_count = QSpinBox()
        self.option_count.setRange(2, MULTIPLE_CHOICE_MAX_COUNT)
        self.option_count.setValue(MULTIPLE_CHOICE_DEFAULT_COUNT)

        self.style_application = QComboBox()
        self.style_application.addItem("Fixed style", "fixed")
        self.style_application.addItem("Style using tags", "tags")

        self.palette = QComboBox()
        self.palette.addItem(PALETTE_NAMES["base"], "base")
        self.palette.insertSeparator(self.palette.count())
        for color in COLORS:
            self.palette.addItem(color, color.lower())
        self.palette.insertSeparator(self.palette.count())
        for country, code, slug in COUNTRIES:
            flag = "".join(chr(ord(letter) - ord("a") + 0x1F1E6) for letter in code)
            self.palette.addItem(f"{flag}  {country}", f"flag-{slug}")

        self.finish = QComboBox()
        self.centered = QCheckBox("Center card content")
        self.shuffle_default = QCheckBox("Shuffle answers by default")
        self.shuffle_default.setChecked(bool(QSettings("Material Notes", "Material Notes").value(ADDON_CONFIG_KEY, False, type=bool)))
        self.answer_coloring = QComboBox()
        self.answer_coloring.addItem("Show all correct answers", ANSWER_COLORING_ALL)
        self.answer_coloring.addItem("Highlight only mistakes", ANSWER_COLORING_MISTAKES)
        self.answer_coloring.setCurrentIndex(
            self.answer_coloring.findData(configured_answer_coloring())
        )
        self.option_labels = QComboBox()
        self.option_labels.addItem("Letters (A, B, C…)", OPTION_LABELS_LETTERS)
        self.option_labels.addItem("Numbers (1, 2, 3…)", OPTION_LABELS_NUMBERS)
        self.option_labels.addItem("None", OPTION_LABELS_NONE)
        self.option_labels.setToolTip(
            "Numbers identify fields: 1 = Option A, 2 = Option B, and so on. "
            "Labels stay with each answer when shuffled."
        )
        self.update_finishes()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create")
        buttons.accepted.connect(self.create)
        buttons.rejected.connect(self.reject)

        template_group = QGroupBox("Note type")
        template_layout = QFormLayout(template_group)
        template_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        template_layout.addRow("Template", self.kind)
        template_layout.addRow("", self.description)
        template_layout.addRow("Note type name (optional)", self.name)
        template_layout.addRow("Number of answer options", self.option_count)
        template_layout.addRow("Fields to create", self.fields)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        appearance_layout.addRow("Style application", self.style_application)

        self.fixed_controls = QWidget()
        fixed_layout = QFormLayout(self.fixed_controls)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        fixed_layout.addRow("Palette", self.palette)
        fixed_layout.addRow("Finish", self.finish)
        fixed_layout.addRow("", self.centered)
        appearance_layout.addRow(self.fixed_controls)
        appearance_layout.addRow("Shuffle answers by default", self.shuffle_default)
        appearance_layout.addRow("Answer feedback", self.answer_coloring)
        appearance_layout.addRow("Option labels", self.option_labels)

        self.tag_controls = QWidget()
        tag_layout = QVBoxLayout(self.tag_controls)
        tag_layout.setContentsMargins(0, 0, 0, 0)
        tag_help = QLabel(
            "Add one style tag in Anki’s Tags field to set each note’s appearance. "
            "All cards from the same note share its tags."
        )
        tag_help.setWordWrap(True)
        tag_layout.addWidget(tag_help)

        self.tag_examples = QComboBox()
        self.tag_examples.setAccessibleName("Style tag examples")
        self.tag_examples.addItems(STYLE_TAG_EXAMPLES)
        self.copy_tag = QPushButton("Copy tag")
        self.copy_tag.setAutoDefault(False)
        self.copy_tag.clicked.connect(self.copy_style_tag)
        self.tag_examples.currentIndexChanged.connect(lambda: self.copy_tag.setText("Copy tag"))
        example_layout = QHBoxLayout()
        example_layout.addWidget(self.tag_examples, 1)
        example_layout.addWidget(self.copy_tag)
        tag_layout.addLayout(example_layout)

        guide = QLabel(f'<a href="{GUIDE_URL}">📖 How to use style tags ↗</a>')
        guide.setOpenExternalLinks(True)
        guide.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        tag_layout.addWidget(guide)
        appearance_layout.addRow(self.tag_controls)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(template_group)
        layout.addWidget(appearance_group)
        layout.addWidget(buttons)
        self.kind.currentIndexChanged.connect(self.update_preview)
        self.option_count.valueChanged.connect(self.update_preview)
        self.style_application.currentIndexChanged.connect(self.update_style_application)
        self.palette.currentIndexChanged.connect(self.update_finishes)
        self.finish.currentIndexChanged.connect(self.update_suggested_name)
        self.update_preview()
        self.update_style_application()

    def suggested_name(self):
        return suggest_note_type_name(
            self.models, self.kind.currentData(), self.style_application.currentData(),
            self.palette.currentData(), self.finish.currentData(),
        )

    def update_suggested_name(self):
        self.name.setPlaceholderText(self.suggested_name())

    def update_preview(self):
        kind = self.kind.currentData()
        preset = NOTE_TYPES[kind]
        self.update_suggested_name()
        self.description.setText(preset["description"])
        self.option_count.setVisible(kind == MULTIPLE_CHOICE_KIND)
        self.fields.setText(", ".join(preset_fields(
            kind, preset, self.option_count.value() if kind == MULTIPLE_CHOICE_KIND else None
        )))

    def update_finishes(self):
        selected = self.finish.currentData()
        signals_blocked = self.finish.blockSignals(True)
        self.finish.clear()
        for finish in available_finishes(self.palette.currentData()):
            self.finish.addItem(FINISHES[finish], finish)
        self.finish.setCurrentIndex(max(0, self.finish.findData(selected)))
        self.finish.blockSignals(signals_blocked)
        self.update_suggested_name()

    def update_style_application(self):
        using_tags = self.style_application.currentData() == "tags"
        self.fixed_controls.setVisible(not using_tags)
        is_multiple_choice = self.kind.currentData() == MULTIPLE_CHOICE_KIND
        self.shuffle_default.setVisible(is_multiple_choice)
        self.answer_coloring.setVisible(is_multiple_choice)
        self.option_labels.setVisible(is_multiple_choice)
        self.tag_controls.setVisible(using_tags)
        self.update_suggested_name()
        self.adjustSize()

    def copy_style_tag(self):
        QApplication.clipboard().setText(self.tag_examples.currentText())
        self.copy_tag.setText("Copied!")

    def create(self):
        name = self.name.text().strip()
        if name and self.models.byName(name):
            showInfo("A note type with that name already exists.", parent=self)
            return
        name = name or self.suggested_name()

        try:
            style_application = self.style_application.currentData()
            shuffle_default = self.shuffle_default.isChecked()
            QSettings("Material Notes", "Material Notes").setValue(ADDON_CONFIG_KEY, shuffle_default)
            answer_coloring = self.answer_coloring.currentData()
            if self.kind.currentData() == MULTIPLE_CHOICE_KIND:
                QSettings("Material Notes", "Material Notes").setValue(
                    ANSWER_COLORING_CONFIG_KEY, answer_coloring
                )
            appearance = {
                "palette": self.palette.currentData(),
                "finish": self.finish.currentData(),
                "centered": self.centered.isChecked(),
            } if style_application == "fixed" else None
            create_note_type(
                self.models, self.kind.currentData(), name, appearance, style_application,
                shuffle_default,
                self.option_count.value() if self.kind.currentData() == MULTIPLE_CHOICE_KIND else None,
                answer_coloring,
                option_labels=self.option_labels.currentData(),
            )
        except (AnkiError, OSError) as error:
            showInfo(str(error), parent=self, textFormat=Qt.TextFormat.PlainText)
            return
        self.accept()


class EditNoteTypeDialog(QDialog):
    def __init__(self, parent, models, model, confirm_overwrite):
        super().__init__(parent)
        self.models = models
        self.model = model
        self.confirm_overwrite = confirm_overwrite
        self.setWindowTitle("Edit note type settings")
        self.setMinimumWidth(520)

        kind = model.get("mfc_kind", "basic")
        preset = NOTE_TYPES[kind]
        self.is_multiple_choice = kind == MULTIPLE_CHOICE_KIND
        self.style_application = QComboBox()
        self.style_application.addItem("Fixed style", "fixed")
        self.style_application.addItem("Style using tags", "tags")
        current_style = model.get("mfc_style_application", "legacy")
        if current_style not in {"fixed", "tags"}:
            current_style = "tags"
        self.style_application.setCurrentIndex(self.style_application.findData(current_style))

        old_appearance = model.get("mfc_appearance", {})
        self.fixed_appearance = {
            "palette": old_appearance.get("palette", "base"),
            "finish": old_appearance.get("finish", "base"),
            "centered": bool(old_appearance.get("centered", False)),
        }
        self.palette = QComboBox()
        self.palette.addItem(PALETTE_NAMES["base"], "base")
        self.palette.insertSeparator(self.palette.count())
        for color in COLORS:
            self.palette.addItem(color, color.lower())
        self.palette.insertSeparator(self.palette.count())
        for country, code, slug in COUNTRIES:
            flag = "".join(chr(ord(letter) - ord("a") + 0x1F1E6) for letter in code)
            self.palette.addItem(f"{flag}  {country}", f"flag-{slug}")
        self.palette.setCurrentIndex(
            max(0, self.palette.findData(old_appearance.get("palette", "base")))
        )

        self.finish = QComboBox()
        self.centered = QCheckBox("Center card content")
        self.centered.setChecked(bool(old_appearance.get("centered", False)))
        self.fixed_controls = QWidget()
        fixed_layout = QFormLayout(self.fixed_controls)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        fixed_layout.addRow("Palette", self.palette)
        fixed_layout.addRow("Finish", self.finish)
        fixed_layout.addRow("", self.centered)
        self.tags_help = QLabel(
            "The palette and layout come from each note’s tags while this mode is selected."
        )
        self.tags_help.setWordWrap(True)

        self.option_count = QSpinBox()
        current_count = multiple_choice_option_count(
            model, default=preset.get("option_count_default", MULTIPLE_CHOICE_DEFAULT_COUNT)
        ) if self.is_multiple_choice else MULTIPLE_CHOICE_DEFAULT_COUNT
        self.option_count.setRange(current_count, MULTIPLE_CHOICE_MAX_COUNT)
        self.option_count.setValue(current_count)

        self.shuffle_default = QCheckBox("Shuffle when Shuffle Options is blank")
        self.shuffle_default.setChecked(bool(model.get("mfc_shuffle_default", False)))
        self.shuffle_policy = QComboBox()
        self.shuffle_policy.addItem("Use each note’s Shuffle Options field", SHUFFLE_POLICY_FIELD)
        self.shuffle_policy.addItem("Always shuffle", SHUFFLE_POLICY_ALWAYS)
        self.shuffle_policy.addItem("Never shuffle", SHUFFLE_POLICY_NEVER)
        policy = model.get("mfc_shuffle_policy", SHUFFLE_POLICY_FIELD)
        self.shuffle_policy.setCurrentIndex(max(0, self.shuffle_policy.findData(policy)))

        self.answer_coloring = QComboBox()
        self.answer_coloring.addItem("Show all correct answers", ANSWER_COLORING_ALL)
        self.answer_coloring.addItem("Highlight only mistakes", ANSWER_COLORING_MISTAKES)
        coloring = model.get("mfc_answer_coloring", ANSWER_COLORING_ALL)
        self.answer_coloring.setCurrentIndex(max(0, self.answer_coloring.findData(coloring)))
        self.option_labels = QComboBox()
        self.option_labels.addItem("Letters (A, B, C…)", OPTION_LABELS_LETTERS)
        self.option_labels.addItem("Numbers (1, 2, 3…)", OPTION_LABELS_NUMBERS)
        self.option_labels.addItem("None", OPTION_LABELS_NONE)
        self.option_labels.setToolTip(
            "Numbers identify fields: 1 = Option A, 2 = Option B, and so on. "
            "Labels stay with each answer when shuffled."
        )
        labels = model.get("mfc_option_labels", OPTION_LABELS_LETTERS)
        self.option_labels.setCurrentIndex(max(0, self.option_labels.findData(labels)))

        note_group = QGroupBox("Note type")
        note_layout = QFormLayout(note_group)
        note_layout.addRow("Name", QLabel(model["name"]))
        note_layout.addRow("Style application", self.style_application)
        note_layout.addRow(self.fixed_controls)
        note_layout.addRow(self.tags_help)

        self.multiple_choice_controls = QWidget()
        mc_layout = QFormLayout(self.multiple_choice_controls)
        mc_layout.setContentsMargins(0, 0, 0, 0)
        mc_layout.addRow("Number of options", self.option_count)
        mc_layout.addRow("Default shuffle", self.shuffle_default)
        mc_layout.addRow("Shuffle behavior", self.shuffle_policy)
        mc_layout.addRow("Answer feedback", self.answer_coloring)
        mc_layout.addRow("Option labels", self.option_labels)
        note_layout.addRow(self.multiple_choice_controls)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.save)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(note_group)
        layout.addWidget(buttons)
        self.style_application.currentIndexChanged.connect(self.update_style_controls)
        self.palette.currentIndexChanged.connect(self.palette_changed)
        self.finish.currentIndexChanged.connect(self.remember_fixed_appearance)
        self.centered.toggled.connect(self.remember_fixed_appearance)
        self.update_finishes()
        self.update_style_controls()

    def update_style_controls(self):
        fixed_style = self.style_application.currentData() == "fixed"
        self.fixed_controls.setVisible(fixed_style)
        self.tags_help.setVisible(not fixed_style)
        self.multiple_choice_controls.setVisible(self.is_multiple_choice)
        self.adjustSize()

    def palette_changed(self):
        self.update_finishes()
        self.remember_fixed_appearance()

    def update_finishes(self):
        selected = self.finish.currentData()
        self.finish.clear()
        for finish in available_finishes(self.palette.currentData()):
            self.finish.addItem(FINISHES[finish], finish)
        self.finish.setCurrentIndex(max(0, self.finish.findData(selected or "base")))
        self.remember_fixed_appearance()

    def remember_fixed_appearance(self, *_):
        self.fixed_appearance = {
            "palette": self.palette.currentData() or "base",
            "finish": self.finish.currentData() or "base",
            "centered": self.centered.isChecked(),
        }

    def save(self):
        style_application = self.style_application.currentData()
        appearance = self.fixed_appearance if style_application == "fixed" else None
        try:
            result = edit_note_type_settings(
                self.models, self.model, appearance, style_application,
                self.shuffle_default.isChecked(), self.option_count.value(),
                self.answer_coloring.currentData(), self.shuffle_policy.currentData(),
                self.option_labels.currentData(), self.confirm_overwrite,
            )
        except (AnkiError, OSError) as error:
            showInfo(str(error), parent=self, textFormat=Qt.TextFormat.PlainText)
            return
        if result == "skipped":
            showInfo("The settings were not applied.", parent=self)
            return
        if result == "incompatible":
            showInfo("This note type is no longer compatible with the preset.", parent=self)
            return
        self.accept()


class NoteTypesDialog(QDialog):
    def __init__(self, parent, models):
        super().__init__(parent)
        self.models = models
        self.setWindowTitle("Material Notes")
        self.resize(460, 300)

        self.note_types = QListWidget()
        self.note_types.setAccessibleName("Managed note types")
        self.empty_message = QLabel("No Material note types in this collection yet.")
        self.details = QLabel("Select a note type to see its settings.")
        self.details.setWordWrap(True)
        self.edit_button = QPushButton("Edit settings…")
        self.edit_button.setEnabled(False)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        create = QPushButton("Create note type…")
        self.update_button = QPushButton("Update note types")
        buttons.addButton(create, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.edit_button, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.update_button, QDialogButtonBox.ButtonRole.ActionRole)
        create.clicked.connect(self.create)
        self.edit_button.clicked.connect(self.edit_selected)
        self.update_button.clicked.connect(self.update_note_types)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Material note types in this collection"))
        layout.addWidget(self.note_types)
        layout.addWidget(self.details)
        layout.addWidget(self.empty_message)
        layout.addWidget(buttons)
        self.note_types.currentItemChanged.connect(self.show_selected_details)
        self.refresh()

    def refresh(self):
        note_types = managed_note_types(self.models)
        self.note_types.clear()
        for model in note_types:
            version = css_version(model.get("css", ""))
            label = f"CSS v{version}" if version else "CSS version unknown"
            self.note_types.addItem(f"{model['name']} — {label}")
            self.note_types.item(self.note_types.count() - 1).setData(
                Qt.ItemDataRole.UserRole, model["name"]
            )
        self.empty_message.setVisible(not note_types)
        self.update_button.setEnabled(bool(note_types))
        if note_types:
            self.note_types.setCurrentRow(0)
        else:
            self.show_selected_details()

    def show_selected_details(self, *_):
        item = self.note_types.currentItem()
        name = item.data(Qt.ItemDataRole.UserRole) if item else None
        model = self.models.byName(name) if name else None
        self.edit_button.setEnabled(model is not None)
        if model is None:
            self.details.setText("Select a note type to see its settings.")
            return

        kind = model.get("mfc_kind", "basic")
        appearance = model.get("mfc_appearance", {})
        if model.get("mfc_style_application", "fixed") == "tags":
            style = "Style using tags"
        else:
            palette = PALETTE_NAMES.get(appearance.get("palette", "base"), "Default")
            finish = FINISHES.get(appearance.get("finish", "base"), "Base")
            style = f"{palette} · {finish}"
            if appearance.get("centered"):
                style += " · centered"
        lines = [f"Template: {NOTE_TYPES[kind]['label']}", f"Style: {style}"]
        if kind == MULTIPLE_CHOICE_KIND:
            lines.append(f"Options: {multiple_choice_option_count(model)}")
            labels = model.get("mfc_option_labels", OPTION_LABELS_LETTERS)
            label_summary = {
                OPTION_LABELS_LETTERS: "letters",
                OPTION_LABELS_NUMBERS: "numbers",
                OPTION_LABELS_NONE: "none",
            }.get(labels, "letters")
            lines.append(f"Option labels: {label_summary}")
            policy = model.get("mfc_shuffle_policy", SHUFFLE_POLICY_FIELD)
            if policy == SHUFFLE_POLICY_ALWAYS:
                shuffle = "always"
            elif policy == SHUFFLE_POLICY_NEVER:
                shuffle = "never"
            else:
                fallback = "shuffle" if model.get("mfc_shuffle_default", False) else "keep order"
                shuffle = f"per note (blank: {fallback})"
            lines.append(f"Shuffle: {shuffle}")
            coloring = model.get("mfc_answer_coloring", ANSWER_COLORING_ALL)
            lines.append(
                "Answer feedback: " +
                ("highlight only mistakes" if coloring == ANSWER_COLORING_MISTAKES else "show all correct answers")
            )
        self.details.setText("\n".join(lines))

    def create(self):
        if CreateNoteTypeDialog(self, self.models).exec():
            self.refresh()
            mw.reset()

    def edit_selected(self):
        item = self.note_types.currentItem()
        name = item.data(Qt.ItemDataRole.UserRole) if item else None
        model = self.models.byName(name) if name else None
        if model and EditNoteTypeDialog(self, self.models, model, self.confirm_overwrite).exec():
            self.refresh()
            mw.reset()

    def confirm_overwrite(self, name):
        return askUser(
            f'The styling or card templates for "{name}" differ from the last installed version.\n\n'
            "Replace the changed styling and templates with the current Material Notes files?",
            parent=self,
            defaultno=True,
        )

    def update_note_types(self):
        try:
            css = read_model_file(MODEL_DIR / "styles.css")
        except OSError as error:
            showInfo(str(error), parent=self, textFormat=Qt.TextFormat.PlainText)
            return

        note_types = managed_note_types(self.models)
        results = []
        updated = False
        for model in note_types:
            try:
                status = update_note_type(self.models, model, css, self.confirm_overwrite)
            except (AnkiError, OSError) as error:
                status = f"could not update ({error})"
            updated = updated or status == "updated"
            results.append(f"{model['name']} — {status}")

        self.refresh()
        if updated:
            mw.reset()
        if results:
            showInfo("\n".join(results), parent=self, textFormat=Qt.TextFormat.PlainText)


def show_note_types():
    if mw.col is not None:
        NoteTypesDialog(mw, mw.col.models).exec()


def setup_menu():
    action = QAction("Material Notes…", mw)
    action.triggered.connect(show_note_types)
    mw.form.menuTools.addAction(action)


gui_hooks.main_window_did_init.append(setup_menu)
