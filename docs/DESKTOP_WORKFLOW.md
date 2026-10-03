# Desktop calibration workflow — 0.2.0

The Mono 4 desktop now connects the existing software-validated backend to project
persistence, preparation, preview and export. It produces **calibration candidates**;
firmware acceptance and physical printing remain unqualified.

## Use

1. Import one closed STL, interpreted in millimetres. Rotate or uniformly scale it,
   then apply the transform; Undo restores the preceding transform. XY placement is
   automatically centered. The displayed model excludes generated supports/raft.
2. Enter normal and bottom exposure values for the actual resin. They start unset.
   Review layer height, bottom-layer count, lift/retract speeds and rest under
   **Layer and motion settings**. Speeds are explicitly mm/min. Defaults are software
   parameters, not a calibrated Anycubic resin preset.
3. Enable **Generate supports and raft** when appropriate. **Slice and validate** runs
   PrusaSlicer 2.9.4, UVTools core 7.0.1, complete pixel/metadata readback and selected
   issue checks. Cancel stops the backend job without making an export available.
4. Inspect actual decoded PM4N layers in **Layers**, including the first/bottom and
   last layers. The image is a reduced display of native pixels, with their horizontal
   mirroring retained. The slider reads one layer at a time; it does not cache an
   entire 10K stack. The model tab remains the unsupported input geometry view.
5. **Export calibration candidate** explicitly confirms the unqualified hardware/resin
   status, copies to the chosen `.pm4n` path and verifies the destination copy before
   atomic publication. A mounted USB directory is an ordinary selectable destination.
   No command starts a printer or unmounts media.

Save/reopen uses `.seesaw` JSON with a hash-bound external STL reference. Keep that STL
in its saved location; missing or changed source files are rejected. Reopening never
restores export readiness. Source, transform and settings changes invalidate prior
results. Project save records applied transforms; unapplied spinbox edits are not saved.

Jobs and diagnostics use `$XDG_CACHE_HOME/progretech-seesaw/jobs` (default
`~/.cache/progretech-seesaw/jobs`), or an explicit `SEESAW_JOB_ROOT`. Each job has a unique
folder with prepared STL, generated allowlisted configuration, logs, archives, candidate
and validation manifest. They remain local and are not automatically deleted. On the
reference workstation, validation artifacts and final packages are kept on PT_CONTEXT.

## Tested scope

Ubuntu 26.04.1 amd64, Python 3.12, Qt/XCB under XWayland, PrusaSlicer 2.9.4 and UVTools
core 7.0.1. Core suite: 87 tests at the initial desktop acceptance point, plus lint.
The optional real desktop smoke exercises STL import, scale/rotation, project reopen,
backend processing, first/last decoded layers, asynchronous verified export and
invalidation after an exposure edit. The 24-layer fixture passed exact pixel readback
and selected issue checks with networking disabled. Fixture exposure numbers are test
inputs only. A separate desktop cancellation run published no candidate. The angled asymmetric
104-layer support/raft fixture also completed the offline desktop workflow with exact
pixel readback. A tiny flat supported fixture produced an island at layer 110; the
application rejected it and removed pending/candidate output. Support generation does
not guarantee printable contacts for every orientation. Open job details exposes the
local diagnostics when validation rejects a job.

```bash
QT_QPA_PLATFORM=xcb uv run python tools/smoke_workflow.py --output /path/to/artifacts
QT_QPA_PLATFORM=xcb uv run python tools/smoke_workflow.py --output /path/to/cancel --cancel
QT_QPA_PLATFORM=xcb uv run python tools/smoke_workflow.py --output /path/to/supports --supports
```

Tests require the pinned native engines and a working display; they are not ordinary
core CI tests. Unit coverage additionally exercises geometry order/nonfinite rejection,
preview dimensions/count/index bounds, and export tamper/cancellation/I/O failures with
preservation of an existing destination. A worker remains logically busy until its Qt
completion handlers run; native thread exit alone does not permit another operation.

## Limits

- One closed mesh, 512 layers maximum, and conservative available-RAM/disk admission.
  Large 10K jobs need profiling before raising that bound.
- Translation is retained in project records but rejected for slicing. Copies,
  auto-orientation, editable support points, hollowing and drain-hole editing remain open.
- No physical resin/firmware qualification, native Wayland/headless qualification,
  Ubuntu 24.04 packaged trial or additional printer qualification is claimed.
- Native engines are separate prerequisites. The `.deb` bundles the Python UI runtime;
  it does not silently fetch slicers or models on launch.
- These checks detect a defined subset of file/geometry issues. They do not certify
  support effectiveness, resin exposure, drainage or a successful print.
