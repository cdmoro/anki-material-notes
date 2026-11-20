import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_SOURCES = ("base", "variants", "elements", "audio", "utils")


def build_css():
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    sections = [
        f"/* {manifest['name']} · {manifest['author']} · {manifest['version']}\n"
        f" * {manifest['homepage']}\n"
        " * Generated from src/styles/ by make build-css.\n"
        " */"
    ]
    for name in STYLE_SOURCES:
        source = (ROOT / "src" / "styles" / f"{name}.css").read_text(encoding="utf-8")
        sections.append(f"/* {name.title()} */\n\n{source.rstrip()}")

    output = ROOT / "models" / "styles.css"
    output.write_text("\n\n".join(sections) + "\n", encoding="utf-8")
    print(output.relative_to(ROOT))


if __name__ == "__main__":
    build_css()
