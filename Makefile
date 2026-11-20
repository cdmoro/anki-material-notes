PYTHON ?= python3

.PHONY: build-css build-card build-addon

build-css:
	$(PYTHON) utils/build_css.py

build-card: build-css
	$(PYTHON) utils/package.py card

build-addon: build-css
	$(PYTHON) utils/package.py addon
