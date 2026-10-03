# Ubuntu installer and updates

Release **0.3.0** provides printer and material selection, saved material profiles,
model placement/copies, supports, sliced-layer preview and verified PM4N/G-code export.
See `WORKSPACE_0_3.md`. Firmware and material settings remain physically unqualified.

PrusaSlicer **2.9.4** and UVTools core **7.0.1** must already be installed. The application
reports missing/mismatched engines; it does not download them during offline use. The
reference workstation has these engines installed. Other machines need a separate engine
installation before slicing; this release is not a complete air-gapped engine bundle.

## Install and launch

Download `progretech-seesaw_0.3.0_amd64.deb` from the project's
[GitHub releases](https://github.com/eabdiel/ProgreTech-Seesaw/releases).
Open it with Ubuntu's package installer, or run:

```bash
sudo apt install ./progretech-seesaw_0.3.0_amd64.deb
```

Find **ProgreTech Seesaw** in the Ubuntu application launcher. The terminal command
is `progretech-seesaw`. Python, Qt/VTK and Python dependencies are bundled under
`/opt/progretech-seesaw`; the development checkout and `uv` are not needed to run it.
System graphics libraries and PolicyKit are declared package dependencies. A normal
Ubuntu desktop generally already has them; initial installation may need apt to
fetch missing system packages. No pip downloads or account login happen on launch.

The first package is tested on Ubuntu 26.04.1 amd64 through X11/XWayland. Ubuntu 24.04
is a compatibility target, not a tested claim. Native Wayland/headless VTK remains
unqualified. CUDA and a model download are not required.

## Check for updates

Click **Check for updates** in the top-right of the application. This is the only
automatic-release network operation and occurs only at your request. It uses the
public GitHub API for this repository's latest published, non-prerelease release.
It never pulls `main`, runs Git hooks, changes your source checkout or applies a
partial source update.

If a newer numeric release exists, the app offers to download and install it. The
download is restricted to the project's release asset and approved GitHub HTTPS
hosts, has size/time bounds, and must match the SHA-256 digest supplied by GitHub.
Ubuntu asks for administrator authentication through PolicyKit. A root-owned helper
copies the package into a private directory, rechecks its hash, package name,
architecture and exact version, rejects downgrades and invokes dpkg. Restart from
the success dialog or launcher to use the new version.

There are no background checks or forced updates. An offline or rate-limited check
shows an error and leaves the application usable. Download cancellation removes
the partial file. Installation cannot be interrupted by closing the UI; allow the
package manager to finish. If new system dependencies are missing, install the
release with `sudo apt install ./downloaded-file.deb`; the updater itself stays
offline after downloading the package and does not change unrelated OS packages.

Trust boundary: GitHub HTTPS plus the release digest verifies transport/integrity.
This is not independent publisher signing; someone who controls this repository's
releases can publish an update. Administrator approval remains required to install.

## Uninstall and recovery

```bash
sudo apt remove progretech-seesaw
```

User models are never package-owned or deleted by uninstall. Downloads are temporary
under the user's XDG cache directory. Reinstall a known-good `.deb` with apt if an
upgrade fails; the UI deliberately does not offer silent downgrades. Package-manager
locks/authentication errors are reported without declaring success.

## Rebuild

From a clean checkout with uv-managed Python 3.12:

```bash
uv sync --python 3.12 --extra desktop --extra dev --locked
uv run python tools/build_deb.py --work /path/to/fresh/build --output /path/to/deliverables
```

The build uses locked wheel hashes, preserves their license files and bundles the
Python runtime's notices. Dependency inventory and locked requirements are installed
under `/usr/share/doc/progretech-seesaw/`. The source release includes build scripts;
native runtimes are unmodified upstream binaries. Keep source/licensing references
with every release. On Edwin's workstation, build artifacts and final installers
belong on PT_CONTEXT, as required by AGENTS.md.
