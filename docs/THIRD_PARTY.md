# Third-party components

Seesaw foundation code is AGPL-3.0-only. The repository's LICENSE contains the
standard GNU Affero GPL v3 license text. No slicer implementation has been vendored.

| Component | Role | Reviewed upstream license text |
| --- | --- | --- |
| PrusaSlicer | Planned external engine | AGPL v3 |
| UVTools | Planned external encoder | AGPL v3 |
| mslicer | Optional future engine | GPL v3 |

Exact reviewed revisions and source links are in `BACKEND_REVIEW.md`. A later binary
bundle must include upstream notices, corresponding source/build information and any
patches. Keep license review attached to the actual revisions and dependency inventory.

Python/runtime dependencies are declared in `pyproject.toml` and resolved in `uv.lock`.
Before a redistributable desktop release, inventory their license files, including
PySide6/Qt modules, PyVista, VTK, trimesh, NumPy and transitive dependencies. A working
developer install is not a completed binary redistribution review.

The owner's UI reference is used as design direction, not shipped as an application
asset. No third-party printable model or AI weights are included in this repository.
