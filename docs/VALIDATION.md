# Foundation validation — 2026-10-02

Reference environment: Ubuntu 26.04.1 LTS, x86-64, Python 3.12.14. Exact Python
dependencies are in `uv.lock`. The project is a development foundation, not a printer release.

## Passed

- `uv sync --python 3.12 --extra desktop --extra dev --locked`: installs the project.
- `uv run pytest -q`: eight tests pass. Real generated STL fixtures cover dimensions,
  oversized geometry, open meshes, corrupt/wrong-type input, safe command planning,
  missing profiles and honest backend-discovery status.
- `uv run ruff check .`: no lint findings.
- Wheel and source distribution build with `uv build`.
- Qt/XCB desktop launches and threaded STL import produces expected dimensions/fit.
- VTK framebuffer capture shows the teal fixture and build grid. The repeatable smoke
  tool also requires a nonblank model-colored region.

Run the optional desktop smoke with a working X11 or XWayland display:

```bash
QT_QPA_PLATFORM=xcb uv run python tools/smoke_desktop.py --output /path/to/test-artifacts
```

On the development workstation, test artifacts belong on PT_CONTEXT. The launcher
defaults to XCB when DISPLAY is available and preserves explicit Qt platform overrides.

## Limits and failed probes

- Qt offscreen with VTK's X window failed with BadWindow. Forcing an EGL window also
  produced OpenGL/shader errors. These configurations are not qualified.
- Qt whole-widget capture did not correctly capture the embedded native viewport;
  the native window capture under this desktop returned black. The separate VTK
  framebuffer is visually checked. Full compositor-level screenshot validation and
  hands-on interaction remain pending; do not present the failed captures as UI evidence.
- PrusaSlicer, UVtoolsCmd and mslicer's `slicer` were absent from PATH. No actual backend
  slicing, PM4N encoding, parameter round-trip or physical print was performed.
- No full-network-isolation test, Ubuntu 24.04 package test or native Wayland test yet.
- CI is configured for Python 3.12 and 3.14, but local results above use 3.12.
- Backend source snapshots prove only inspected source capabilities. Firmware acceptance,
  resin exposure, axis orientation, support quality and material calibration are unverified.

The desktop can inspect geometry; its export control stays disabled. The `plan`
command prints research argv arrays without running them. No print-ready claim is made.
