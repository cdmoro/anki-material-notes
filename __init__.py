"""Manage Material Notes note types in the active Anki collection."""

import hashlib
from copy import deepcopy
from pathlib import Path

from anki.consts import MODEL_STD
from anki.errors import AnkiError
from aqt import gui_hooks, mw
from aqt.qt import (
    QAction,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    Qt,
    QVBoxLayout,
)
from aqt.utils import askUser, showInfo

MODEL_DIR = Path(__file__).resolve().parent / "models"
NOTE_TYPES = {
    "basic": ("Basic", "Material (basic)", ("Front", "Back"), MODEL_DIR),
    "multiple-choice": (
        "Multiple choice",
        "Material (multiple choice)",
        ("Question", "Options", "Correct Options", "Explanation"),
        MODEL_DIR / "multiple-choice",
    ),
}


def read_model_file(path):
    return path.read_text(encoding="utf-8")


def template_content(directory):
    return {
        "qfmt": read_model_file(directory / "front.html"),
        "afmt": read_model_file(directory / "back.html"),
    }


def content_hash(*parts):
    return hashlib.sha1("\0".join(parts).encode("utf-8")).hexdigest()


def record_installed_content(model, kind, css, template):
    model["mfc_managed_by_addon"] = True
    model["mfc_kind"] = kind
    model["mfc_original_css_hash"] = content_hash(css)
    model["mfc_template_hash"] = content_hash(template["qfmt"], template["afmt"])


def create_note_type(models, kind, name):
    _, _, fields, directory = NOTE_TYPES[kind]
    model = models.new(name)
    for field in fields:
        models.addField(model, models.newField(field))

    css = read_model_file(MODEL_DIR / "styles.css")
    template = models.newTemplate("Card 1")
    template.update(template_content(directory))
    models.addTemplate(model, template)
    model["css"] = css
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

    _, _, fields, directory = NOTE_TYPES[kind]
    model_fields = {field["name"] for field in model["flds"]}
    if not model_fields.issuperset(fields) or len(model["tmpls"]) != 1:
        return "incompatible"

    installed = model["tmpls"][0]
    latest = template_content(directory)
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

        self.kind = QComboBox()
        for kind, (label, _, _, _) in NOTE_TYPES.items():
            self.kind.addItem(label, kind)
        self.name = QLineEdit()
        self.fields = QLabel()
        self.fields.setWordWrap(True)
        self.kind.currentIndexChanged.connect(self.update_preview)
        self.update_preview()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Create")
        buttons.accepted.connect(self.create)
        buttons.rejected.connect(self.reject)

        layout = QFormLayout(self)
        layout.addRow("Template", self.kind)
        layout.addRow("Name", self.name)
        layout.addRow("Fields", self.fields)
        layout.addRow(buttons)

    def update_preview(self):
        _, default_name, fields, _ = NOTE_TYPES[self.kind.currentData()]
        suggested_name = default_name
        suffix = 2
        while self.models.byName(suggested_name):
            suggested_name = f"{default_name} {suffix}"
            suffix += 1
        self.name.setPlaceholderText(suggested_name)
        self.fields.setText(", ".join(fields))

    def create(self):
        name = self.name.text().strip() or self.name.placeholderText()
        if self.models.byName(name):
            showInfo("A note type with that name already exists.", parent=self)
            return

        try:
            create_note_type(self.models, self.kind.currentData(), name)
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
