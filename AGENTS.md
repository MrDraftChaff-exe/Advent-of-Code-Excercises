# AGENTS.md

## Cursor Cloud specific instructions

This repo is a small Python CLI toolkit (no web app / long-running service) for generating layered, transparent TCG card-frame assets. Everything lives under `frames/`. See `README.md` and `frames/README.md` for the canonical usage examples.

### Runtime & dependencies
- Python 3 with two libraries: `numpy` (preinstalled system-wide) and `Pillow` (installed by the update script into the user site via `pip install --user --break-system-packages`).
- There is no `requirements.txt`, `pyproject.toml`, or package manager config — dependencies are just `numpy` + `Pillow`.

### Lint / test / build
- There is no test suite and no linter/formatter configured in the repo. Do not fabricate one unless asked.
- The closest "build" is byte-compiling the scripts: `python3 -m py_compile frames/*.py`.

### Running the tools (non-obvious caveats)
- Run scripts from the repo root (e.g. `python3 frames/export_layers.py ...`). The scripts contain an import fallback so they work either from the repo root or from inside `frames/`.
- `frames/export_layers.py --compose-only` recomposes `frame.png`/`preview.png` from `layers/*.png` that must **already exist** in `--out-dir`; it will crash with `FileNotFoundError` if the out dir has no `layers/`. To create a fresh pack you must pass a real raster frame via `--punch <raw.png>` (the committed samples under `frames/samples/<id>/frame.png` work well as `--punch` inputs for local end-to-end testing).
- `--punch` is a required argument on `export_layers.py` even in `--compose-only` mode, but its value is ignored when composing (pass any placeholder path).
- Canvas is locked at 750×1050; locked slot geometry lives in `frames/layout.json` and must not be moved.
