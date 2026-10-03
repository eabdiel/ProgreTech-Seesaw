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
asset. The owner-authorized ctrlV test model is bundled unchanged under its supplied CC BY-ND
license (version unspecified). Original README, LICENSE and attribution are packaged
under `seesaw/assets/test-model/`. No AI weights are included.

Flattened MK3S/Generic PLA configuration data comes from the installed PrusaResearch.ini
config_version 2.4.0; provenance is retained in `seesaw/assets/PRUSA_PROFILES_NOTICE.txt`.
The installed PrusaSlicer Debian copyright inventory identifies the source as AGPL-3.
The application license does not relicense the separately attributed model asset.
