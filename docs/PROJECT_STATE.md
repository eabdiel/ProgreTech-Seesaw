# Project persistence and job currency

The Python core now stores a single local STL reference, SHA-256, immutable transform,
explicit optional resin settings, Mono 4 profile identity and revision in versioned JSON.
This is a core API; desktop open/save and preparation integration are still pending.

`Project.from_stl_path(path, settings=...)` records source identity; geometry inspection
still belongs to `model.load_stl`. `save_project` writes a unique temporary file, flushes
it and atomically replaces the destination. It refuses STL destinations. `load_project`
limits JSON size, rejects duplicate/unknown fields and unsupported schemas, validates
types/settings, and rejects missing or changed source files. Models remain external
references; project files do not embed or relocate them. The 256 MiB STL and 64 KiB
project limits bound reads. No arbitrary backend configuration or executable fields
are accepted. Project files include absolute local source paths and should be treated
as local documents when sharing.

Transforms describe translation in millimetres, rotation in degrees, and uniform scale.
This module does not apply them to geometry. The future viewport and slice worker must
share one transform implementation. A saved setting is not a calibrated resin preset.

`project.edited(...)` creates a new revision. `JobGate.begin(project)` produces a unique
input snapshot; `finish(project, snapshot)` rejects stale or superseded completion.
`invalidate()` clears active/completed state. Source changes also invalidate currency.
Undo must create a new revision. Use source checks in an appropriate worker for large
meshes, not repeatedly inside painting callbacks.

The gate proves input currency only. It does **not** validate a printer artifact,
qualify resin/firmware, or authorize export. Reopened projects never restore job state.
The existing pipeline's readback and issue checks remain required before a future UI
can offer a clearly labelled hardware-test candidate.

Validation includes settings round trips, malformed inputs, source tamper/missing
checks, atomic-save failure, source overwrite prevention, fingerprints, stale job
completion, invalidation and reopen without readiness. No desktop or printer feature
is newly claimed by this core-only change.
