import os
import json

ADDON_DIR = os.path.dirname(os.path.dirname(__file__))
SRC_DIR = os.path.join(ADDON_DIR, "src", "styles")
MANIFEST_PATH = os.path.join(ADDON_DIR, "manifest.json")
OUT_FILE = os.path.join(ADDON_DIR, "models", "styles.css")

CSS_FILES = [
    "base",
    "variants",
    "elements",
    "audio",
    "utils"
]

SECTION_COMMENTS = {
    "base": "Basic layout, typography, and core styles",
    "variants": "Different color and style variants for cards",
    "elements": "Buttons, icons, and other UI elements",
    "audio": "Styles for audio playback controls",
}

def load_metadata():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    header = f"""/*
 * Name: {manifest["name"]}
 * Author: {manifest["author"]}
 * Version: {manifest["version"]}
 * Repo: {manifest["homepage"]}
 */
"""

    return header


def build_css():
    print("🔧 Building styles.css...")

    header = load_metadata()
    parts = [header]

    for filename in CSS_FILES:
        print(f" - Appending {filename}.css")
        path = os.path.join(SRC_DIR, f"{filename}.css")

        if not os.path.exists(path):
            print(f"⚠ Warning: CSS not found: {path}")
            continue

        with open(path, "r", encoding="utf-8") as f:
            css = f.read()

            parts.append(f"\n/*** {filename.upper()} ------------------ ***/\n")
            
            if SECTION_COMMENTS.get(filename):
                parts.append(f"/*** {SECTION_COMMENTS[filename]} ***/\n")
            
            parts.append("\n")
            parts.append(css)
            parts.append("\n")

    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("".join(parts))

    print(f"✔ CSS combined → {OUT_FILE}")


if __name__ == "__main__":
    build_css()
