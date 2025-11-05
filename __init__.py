import hashlib
from aqt import mw
from aqt.qt import QAction, QInputDialog, QComboBox, QDialog, QDialogButtonBox, QVBoxLayout, QLabel
from aqt.utils import showInfo, askUser
from aqt import gui_hooks
from anki.tags import TagManager
import os
# from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QVBoxLayout, QLabel, QPushButton
from anki.notes import Note

MODEL_NAME = "Material (basic)"
ADDON_VERSION = 1


# ---------- Utilities ----------

def load_css_from_file():
    addon_dir = os.path.dirname(__file__)
    path = os.path.join(addon_dir, "style.css")
    with open(path, "r", encoding="utf8") as f:
        return f.read()


def get_css_hash(css: str) -> str:
    return hashlib.sha1(css.encode("utf8")).hexdigest()

# ---------- Model management ----------

def ensure_model():
    """Check if the styled model exists, create or update if needed."""
    models = mw.col.models
    model = models.byName(MODEL_NAME)
    css_code = load_css_from_file()
    css_hash = get_css_hash(css_code)

    if not model:
        create_model(models, css_code, css_hash)
        return

    current_css_hash = get_css_hash(model.get("css", ""))
    original_hash = model.get("mfc_original_css_hash")

    if original_hash != current_css_hash:
        if askUser(
            f"The model '{MODEL_NAME}' seems to have been modified by the user.\n\n"
            "Do you want to overwrite it with the latest addon version?",
            defaultno=True,
        ):
            overwrite_model(model, css_code, css_hash)
        else:
            create_new_version_model(models, css_code, css_hash)
    elif original_hash != css_hash:
        overwrite_model(model, css_code, css_hash)
    else:
        return


def create_new_version_model(models, css_code, css_hash):
    base_name = MODEL_NAME
    i = 2
    while models.byName(f"{base_name} {i}"):
        i += 1
    new_name = f"{base_name} {i}"
    create_model(models, css_code, css_hash, model_name=new_name)


def create_model(models, css_code, css_hash, name=MODEL_NAME):
    """Create a new styled note type."""
    model = models.new(name)
    models.addField(model, models.newField("Front"))
    models.addField(model, models.newField("Back"))

    tmpl = models.newTemplate("Card 1")
    tmpl["qfmt"] = "<div class='card {{Tags}}'>{{Front}}</div>"
    tmpl["afmt"] = "{{FrontSide}}<hr id=answer>{{Back}}"
    models.addTemplate(model, tmpl)

    model["css"] = css_code
    model["mfc_original_css_hash"] = css_hash
    model["mfc_version"] = ADDON_VERSION
    model["mfc_managed_by_addon"] = True
    models.add(model)

    showInfo(f"Created new model: {name}")


def overwrite_model(model, css_code, css_hash):
    """Safely overwrite the CSS and templates of an existing model."""
    model["css"] = css_code

    if model.get("tmpls"):
        model["tmpls"][0]["qfmt"] = """<div class="note front {{Tags}}">
    <div class="body center">
        <div class="flex flex-col">{{Front}}</div>
    </div>
</div>"""
        model["tmpls"][0]["afmt"] = """<div class="note back {{Tags}}">
    {{FrontSide}}

    <hr id="answer">

    <div class="body">
        <div class="text-block">
            <div class="flex">{{Back}}</div>
        </div>
    </div>
</div>"""

    model["mfc_original_css_hash"] = css_hash
    model["mfc_version"] = ADDON_VERSION
    mw.col.models.save(model)
    mw.reset()
    showInfo(f"Model '{model['name']}' updated successfully.")


def create_new_model(css_code, css_hash):
    """Ask for a name and create a new styled note type."""
    name, ok = QInputDialog.getText(mw, "New Model", "Enter a name for the new styled model:")
    if ok and name:
        create_model(mw.col.models, css_code, css_hash, name)


# ---------- Migration ----------

class MigrateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Migrate Notes")
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Do you want to migrate notes to the new card type?"))
        
        # Botones Ok y Cancel (PyQt6)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                   QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        
        layout.addWidget(buttons)
        self.setLayout(layout)


def migrate_notes_interactive():
    """Interactive migration using dialog."""
    dlg = MigrateDialog(mw)
    if dlg.exec_():
        old_name, new_name = dlg.get_selection()
        migrate_notes(old_name, new_name)


def migrate_notes(old_name, new_name):
    """Move notes from one model to another if compatible."""
    old_model = mw.col.models.byName(old_name)
    new_model = mw.col.models.byName(new_name)

    if not old_model or not new_model:
        showInfo("Both models must exist to perform the migration.")
        return

    old_fields = [f["name"] for f in old_model["flds"]]
    new_fields = [f["name"] for f in new_model["flds"]]

    if old_fields != new_fields:
        showInfo("The models must have identical fields (Front, Back) to migrate.")
        return

    count = mw.col.db.scalar("select count() from notes where mid = ?", old_model["id"])
    if not count:
        showInfo("No notes found in the source model.")
        return

    if not askUser(f"This will move {count} notes from '{old_name}' to '{new_name}'.\nContinue?"):
        return

    mw.col.db.execute(
        "update notes set mid = ? where mid = ?", new_model["id"], old_model["id"]
    )
    mw.reset()
    showInfo(f"Migrated {count} notes from '{old_name}' to '{new_name}'.")


# ---------- Menu ----------

def setup_menu():
    menu = mw.form.menuTools.addMenu("Flashcard Styles")

    act_overwrite = QAction("Overwrite model", mw)
    act_overwrite.triggered.connect(lambda: ensure_model())
    menu.addAction(act_overwrite)

    act_new = QAction("Create new styled model…", mw)
    act_new.triggered.connect(lambda: create_new_model(load_css_from_file(), get_css_hash(load_css_from_file())))
    menu.addAction(act_new)

    # act_migrate = QAction("Migrate notes…", mw)
    # act_migrate.triggered.connect(migrate_notes_interactive)
    # menu.addAction(act_migrate)


# ---------- Initialization ----------

def on_init():
    ensure_model()
    setup_menu()


gui_hooks.main_window_did_init.append(on_init)
