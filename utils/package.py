import argparse
from zipfile import ZIP_DEFLATED, ZipFile

from build_css import ROOT

CARD_FILES = ("front.html", "back.html", "styles.css")


def package(target):
    output_dir = ROOT / "dist"
    output_dir.mkdir(exist_ok=True)
    if target == "card":
        archive = output_dir / "material-notes-card.zip"
        files = [(ROOT / "models" / name, name) for name in CARD_FILES]
    else:
        archive = output_dir / "material-notes.ankiaddon"
        paths = (
            "__init__.py",
            "manifest.json",
            *(f"models/{name}" for name in CARD_FILES),
            "models/multiple-choice/front.html",
            "models/multiple-choice/back.html",
        )
        files = [(ROOT / name, name) for name in paths]

    with ZipFile(archive, "w", compression=ZIP_DEFLATED) as output:
        for source, name in files:
            output.write(source, name)

    print(archive.relative_to(ROOT))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=("card", "addon"))
    package(parser.parse_args().target)
