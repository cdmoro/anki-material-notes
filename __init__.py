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
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.utils import askUser, showInfo

MODEL_DIR = Path(__file__).resolve().parent / "models"
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


def read_model_file(path):
    return path.read_text(encoding="utf-8")


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


def template_content(preset, appearance=None, style_application="fixed"):
    classes = [] if style_application == "tags" else appearance_classes(**(appearance or {}))
    if style_application != "fixed":
        classes.append("{{Tags}}")
    replacement = " " + " ".join(classes) if classes else ""
    return {
        key: read_model_file(MODEL_DIR / preset[side]).replace(" {{Tags}}", replacement, 1)
        for key, side in (("qfmt", "front"), ("afmt", "back"))
    }


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


def create_note_type(models, kind, name, appearance=None, style_application="fixed"):
    preset = NOTE_TYPES[kind]
    model = models.new(name)
    for field in preset["fields"]:
        models.addField(model, models.newField(field))

    css = read_model_file(MODEL_DIR / "styles.css")
    template = models.newTemplate("Card 1")
    template.update(template_content(preset, appearance, style_application))
    models.addTemplate(model, template)
    model["css"] = css
    model["mfc_style_application"] = style_application
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
    model_fields = {field["name"] for field in model["flds"]}
    if not model_fields.issuperset(preset["fields"]) or len(model["tmpls"]) != 1:
        return "incompatible"

    installed = model["tmpls"][0]
    latest = template_content(
        preset, model.get("mfc_appearance"), model.get("mfc_style_application", "legacy")
    )
    css_changed = css != model["css"]
    template_changed = any(installed[key] != value for key, value in latest.items())
    if not css_changed and not template_changed:
        return "up to date"

    custom_css = css_changed and model.get("mfc_original_css_hash") != content_hash(model["css"])
    custom_template = template_changed and model.get("mfc_template_hash") != content_hash(
        installed["qfmt"], installed["afmt"]
    )
    if (custom_css or custom_template) and not confirm_overwrite(model["name"]):
        return "skipped"

    updated = deepcopy(model)
    updated["css"] = css
    updated["tmpls"][0].update(latest)
    record_installed_content(updated, kind, css, latest)
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
            self.kind.addItem(preset["label"], kind)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setMinimumHeight(44)
        self.name = QLineEdit()
        self.fields = QLabel()
        self.fields.setWordWrap(True)
        self.fields.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

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
        preset = NOTE_TYPES[self.kind.currentData()]
        self.update_suggested_name()
        self.description.setText(preset["description"])
        self.fields.setText(", ".join(preset["fields"]))

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
            appearance = {
                "palette": self.palette.currentData(),
                "finish": self.finish.currentData(),
                "centered": self.centered.isChecked(),
            } if style_application == "fixed" else None
            create_note_type(
                self.models, self.kind.currentData(), name, appearance, style_application
            )
        except (AnkiError, OSError) as error:
            showInfo(str(error), parent=self, textFormat=Qt.TextFormat.PlainText)
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

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        create = QPushButton("Create note type…")
        self.update_button = QPushButton("Update note types")
        buttons.addButton(create, QDialogButtonBox.ButtonRole.ActionRole)
        buttons.addButton(self.update_button, QDialogButtonBox.ButtonRole.ActionRole)
        create.clicked.connect(self.create)
        self.update_button.clicked.connect(self.update_note_types)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Material note types in this collection"))
        layout.addWidget(self.note_types)
        layout.addWidget(self.empty_message)
        layout.addWidget(buttons)
        self.refresh()

    def refresh(self):
        note_types = managed_note_types(self.models)
        self.note_types.clear()
        for model in note_types:
            version = css_version(model.get("css", ""))
            label = f"CSS v{version}" if version else "CSS version unknown"
            self.note_types.addItem(f"{model['name']} — {label}")
        self.empty_message.setVisible(not note_types)
        self.update_button.setEnabled(bool(note_types))

    def create(self):
        if CreateNoteTypeDialog(self, self.models).exec():
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
