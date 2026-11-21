"""Manage Material Notes note types in the active Anki collection."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

from anki.consts import MODEL_STD
from anki.errors import AnkiError
from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    Qt,
    QVBoxLayout,
)
from aqt.utils import askUser, showInfo

MODEL_DIR = Path(__file__).resolve().parent / "models"
NOTE_TYPES = json.loads((MODEL_DIR / "presets.json").read_text(encoding="utf-8"))
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
FINISHES = {"base": "Accent", "filled": "Filled", "outlined": "Outlined"}


def read_model_file(path):
    return path.read_text(encoding="utf-8")


def available_finishes(palette):
    if palette == "base":
        return ("base", "outlined")
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


def template_content(preset, appearance=None):
    classes = " ".join([*appearance_classes(**(appearance or {})), "{{Tags}}"])
    return {
        key: read_model_file(MODEL_DIR / preset[side]).replace("{{Tags}}", classes, 1)
        for key, side in (("qfmt", "front"), ("afmt", "back"))
    }


def content_hash(*parts):
    return hashlib.sha1("\0".join(parts).encode("utf-8")).hexdigest()


def record_installed_content(model, kind, css, template):
    model["mfc_managed_by_addon"] = True
    model["mfc_kind"] = kind
    model["mfc_original_css_hash"] = content_hash(css)
    model["mfc_template_hash"] = content_hash(template["qfmt"], template["afmt"])


def create_note_type(models, kind, name, appearance=None):
    preset = NOTE_TYPES[kind]
    model = models.new(name)
    for field in preset["fields"]:
        models.addField(model, models.newField(field))

    css = read_model_file(MODEL_DIR / "styles.css")
    template = models.newTemplate("Card 1")
    template.update(template_content(preset, appearance))
    models.addTemplate(model, template)
    model["css"] = css
    if appearance:
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
    latest = template_content(preset, model.get("mfc_appearance"))
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
        self.fields.setMinimumHeight(44)
        self.kind.currentIndexChanged.connect(self.update_preview)

        self.palette = QComboBox()
        self.palette.addItem("Default", "base")
        self.palette.insertSeparator(self.palette.count())
        for color in COLORS:
            self.palette.addItem(color, color.lower())
        self.palette.insertSeparator(self.palette.count())
        for country, code, slug in COUNTRIES:
            flag = "".join(chr(ord(letter) - ord("a") + 0x1F1E6) for letter in code)
            self.palette.addItem(f"{flag}  {country}", f"flag-{slug}")

        self.finish = QComboBox()
        self.centered = QCheckBox("Center card content")
        self.palette.currentIndexChanged.connect(self.update_finishes)
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
        template_layout.addRow("Name", self.name)
        template_layout.addRow("Fields", self.fields)

        appearance_group = QGroupBox("Appearance")
        appearance_layout = QFormLayout(appearance_group)
        appearance_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        appearance_layout.addRow("Palette", self.palette)
        appearance_layout.addRow("Finish", self.finish)
        appearance_layout.addRow("", self.centered)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(template_group)
        layout.addWidget(appearance_group)
        layout.addWidget(buttons)
        self.update_preview()

    def update_preview(self):
        preset = NOTE_TYPES[self.kind.currentData()]
        default_name = f"Material ({preset['label'].lower()})"
        suggested_name = default_name
        suffix = 2
        while self.models.byName(suggested_name):
            suggested_name = f"{default_name} {suffix}"
            suffix += 1
        self.name.setPlaceholderText(suggested_name)
        self.description.setText(preset["description"])
        self.fields.setText(", ".join(preset["fields"]))

    def update_finishes(self):
        selected = self.finish.currentData()
        self.finish.clear()
        for finish in available_finishes(self.palette.currentData()):
            self.finish.addItem(FINISHES[finish], finish)
        self.finish.setCurrentIndex(max(0, self.finish.findData(selected)))

    def create(self):
        name = self.name.text().strip() or self.name.placeholderText()
        if self.models.byName(name):
            showInfo("A note type with that name already exists.", parent=self)
            return

        try:
            appearance = {
                "palette": self.palette.currentData(),
                "finish": self.finish.currentData(),
                "centered": self.centered.isChecked(),
            }
            create_note_type(self.models, self.kind.currentData(), name, appearance)
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
        self.note_types.addItems([model["name"] for model in note_types])
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
