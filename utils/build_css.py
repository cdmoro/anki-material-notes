import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLE_SOURCES = ("base", "variants", "elements", "audio", "utils")
GUIDE = ROOT / "docs" / "using-style-tags.md"
CATALOG_START = "<!-- BEGIN STYLE TAG CATALOG -->"
CATALOG_END = "<!-- END STYLE TAG CATALOG -->"
TAG_SELECTOR = re.compile(r"\.note:is\(\.(note-[a-z0-9-]+), \.Material\\:\\:\1\)")
CARD_SETUP_TEMPLATES = "multiple-choice-2"


def style_tags(css):
    return set(TAG_SELECTOR.findall(css))


def render_catalog(tags):
    finishes = ("base", "filled", "outlined")
    palettes = {
        tag[5:].rsplit("-", 1)[0] for tag in tags if tag.endswith(("-base", "-filled", "-outlined"))
    }
    palettes = sorted(palettes, key=lambda palette: (palette != "base", palette.startswith("flag-"), palette))
    names = {"base": "Default", "flag-uk": "United Kingdom", "flag-usa": "USA"}
    lines = [
        "| Palette | Base | Filled | Outlined | Base alias |",
        "| --- | --- | --- | --- | --- |",
    ]
    for palette in palettes:
        label = names.get(palette, palette.removeprefix("flag-").replace("-", " ").title())
        variants = [f"note-{palette}-{finish}" for finish in finishes]
        cells = [f"`{tag}`" if tag in tags else "—" for tag in (*variants, f"note-{palette}")]
        lines.append("| " + " | ".join([label, *cells]) + " |")
    return "\n".join(lines)


def update_guide_catalog(guide, css):
    before, start, rest = guide.partition(CATALOG_START)
    _, end, after = rest.partition(CATALOG_END)
    if not start or not end:
        raise ValueError("Missing style tag catalog markers in the guide")
    return before + start + "\n\n" + render_catalog(style_tags(css)) + "\n\n" + end + after


def render_card_setup_sources(css):
    templates = {
        name: (ROOT / "models" / CARD_SETUP_TEMPLATES / f"{name}.html").read_text(encoding="utf-8")
        for name in ("front", "back")
    }
    # The website's copyable example uses four choices even though the add-on
    # preset supports up to ten.
    templates["front"] = re.sub(
        r"\s*\{\{#Option [E-J]\}\}.*?\{\{/Option [E-J]\}\}",
        "",
        templates["front"],
        flags=re.DOTALL,
    )
    payload = json.dumps({"styles": css, "templates": {CARD_SETUP_TEMPLATES: templates}})
    return f"window.materialNotesSources = {payload};\n"


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
    css = "\n\n".join(sections) + "\n"
    output.write_text(css, encoding="utf-8")
    print(output.relative_to(ROOT))
    sources = ROOT / "src" / "js" / "card-setup-sources.js"
    sources.write_text(render_card_setup_sources(css), encoding="utf-8")
    print(sources.relative_to(ROOT))
    guide = GUIDE.read_text(encoding="utf-8")
    updated_guide = update_guide_catalog(guide, css)
    if updated_guide != guide:
        GUIDE.write_text(updated_guide, encoding="utf-8")
        print(GUIDE.relative_to(ROOT))


if __name__ == "__main__":
    build_css()
