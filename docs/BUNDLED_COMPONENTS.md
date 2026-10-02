# Bundled runtime notices and source access

Seesaw is AGPL-3.0-only. It uses dynamically loaded, unmodified Qt for Python
6.11.2 (PySide6 Essentials and Shiboken), offered under LGPL-3.0, and Qt 6.11.2.
Qt is copyright The Qt Company Ltd. and other contributors. License texts copied
from the exact Qt for Python source archive are installed in
`/usr/share/doc/progretech-seesaw/licenses/qt-for-python/`.

Corresponding upstream source and build instructions are available without charge:

- [Qt for Python / Shiboken 6.11.2 complete source](https://download.qt.io/official_releases/QtForPython/pyside6/PySide6-6.11.2-src/pyside-setup-everywhere-src-6.11.2.tar.xz)
- [Qt 6.11.2 complete source](https://download.qt.io/archive/qt/6.11/6.11.2/single/qt-everywhere-src-6.11.2.tar.xz)
- [Qt for Python build documentation](https://doc.qt.io/qtforpython-6/building_from_source/index.html)
- [Qt Linux source build documentation](https://doc.qt.io/qt-6/linux-building.html)
- [Seesaw source and packaging scripts](https://github.com/eabdiel/ProgreTech-Seesaw)

These source links must also accompany the binary on each GitHub release page.
Seesaw does not modify those libraries or prevent replacing/debugging them. The
libraries are normal shared objects under `/opt/progretech-seesaw/site/`; use the
source build to replace compatible PySide6/Shiboken/Qt binaries, or rebuild the
package using `tools/build_deb.py`. Reverse engineering for debugging modifications
to LGPL libraries is permitted. No proprietary Seesaw license restricts these rights.

The bundled Python 3.12.14 runtime comes from uv's python-build-standalone distribution;
its Python license files remain in the runtime. Other Python/native dependencies
retain the notices included in their wheel distributions. An installed dependency
inventory and exact wheel requirements are under `/usr/share/doc/progretech-seesaw/`.
No PrusaSlicer, UVTools, mslicer or model weights are bundled in release 0.1.0.
