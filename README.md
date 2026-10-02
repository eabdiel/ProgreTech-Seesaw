# ProgreTech Seesaw

A Python-driven, fully offline slicing workflow for Ubuntu. Start with the Anycubic
Photon Mono 4, then qualify more resin printers and add FDM through backend adapters.

**Status: project foundation, not a print-ready slicer.** The desktop can import and
display STL geometry and report dimensions, watertightness and unrotated fit. It cannot
yet prepare supports, slice or export printer files. Nothing in this release should
be treated as a validated Mono 4 print job.

Release **0.1.1** adds an experimental CLI backend-validation path. Actual PrusaSlicer
2.9.4 and UVTools 7.0.1 produced and verified Mono 4 research candidates offline,
including a supported 104-layer fixture. This is separate from the read-only desktop;
see [backend validation and its limits](docs/BACKEND_VALIDATION.md).

The intended production pipeline is:

```text
STL → PrusaSlicer (geometry, supports, layer rasterization)
    → SL1 layer archive → UVTools (inspection and encoding)
    → validated PM4N → USB → Photon Mono 4
```

UVTools' documented PrusaSlicer integration consumes **sliced SL1 archives**, not an
STL-to-printer workflow. The reviewed UVTools v7.0.1 source includes `.pm4n` support.
The proposed backend pairing still needs integration and physical-printer testing.
See the [technical specification](docs/TECHNICAL_SPEC.md),
[backend evidence](docs/BACKEND_REVIEW.md) and [milestones](docs/ROADMAP.md).

## Development setup

For the Ubuntu launcher installation, use the `.deb` from
[GitHub Releases](https://github.com/eabdiel/ProgreTech-Seesaw/releases).
See [installation and manual self-updates](docs/INSTALLATION.md).
The desktop's **Check for updates** button checks published releases only when clicked.
This first installer remains a foundation preview, not a printer-ready slicer.

Python 3.12 is the reference interpreter. Core dependencies are locked in `uv.lock`;
the desktop uses PySide6 and PyVista/VTK. Setup downloads dependencies; application
operation is intended to remain offline. An air-gapped installer is a later milestone.

```bash
uv sync --python 3.12 --extra desktop --extra dev --locked
uv run seesaw-desktop
uv run seesaw doctor
uv run seesaw inspect /path/to/model.stl
uv run pytest -q
uv run ruff check .
```

Open this directory in PyCharm and select `.venv/bin/python` as the interpreter.
Create a Python run configuration with module `seesaw.app` and this directory as its
working directory. OpenGL/EGL and the appropriate Qt platform libraries must be
available for the desktop renderer; see [validation](docs/VALIDATION.md).

For core-only development: `uv sync --python 3.12 --extra dev --locked`.
`seesaw doctor` only checks PATH; it does not certify installed versions or detect
Flatpak packages. `seesaw plan` prints a research command sequence without executing it:

```bash
uv run seesaw plan /path/to/model.stl --profile /path/to/trusted-sla.ini --work-dir /path/to/scratch
```

That plan is not a production export command. The profile must include complete
SLA settings; printer dimensions alone are insufficient. Never execute untrusted
post-processing embedded in imported profiles.

## Product direction

- One local desktop workflow: Add model → Prepare → Preview → Export.
- Reuse PrusaSlicer and UVTools before creating custom geometry or encoder code.
- Benchmark mslicer behind an optional adapter after the reference path is correct.
- No account, telemetry, cloud slicing, runtime update checks or model downloads.
- Later: optional local image/text-to-3D orchestration with per-model hardware checks;
  no bundled weights and no CUDA requirement for ordinary slicing.

Initial material: **Anycubic clear water-washable resin**. Exact product variant,
exposure, temperature and motion settings are not yet qualified.

## License and upstream work

Seesaw code is AGPL-3.0-only; see [LICENSE](LICENSE).
The foundation does not bundle or copy upstream slicer implementation code.
PrusaSlicer and UVTools use AGPL-3.0 license texts; mslicer uses GPL-3.0.
See [third-party notices](docs/THIRD_PARTY.md) before distributing backend binaries.

The UI direction follows the owner's supplied classroom-slicer reference: clear
steps, a large model view, model tools at left, printer/material setup at right and
plain-language status below. Resin terminology replaces the reference's filament controls.
