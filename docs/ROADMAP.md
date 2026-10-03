# Milestones and acceptance

No fixed dates are assigned before backend integration measurements.

## M0 — project foundation

- Technical specification, backend source review, license and reproducible Python environment.
- Native desktop STL import/viewport, dimensional/topology inspection and explicit qualification state.
- Backend PATH diagnostics and nonexecuting research command plan.
- Unit tests and CI; public repository and PyCharm entry point.
- No slicing, supports, project persistence or printer export is claimed in M0.

## M1 — prove Mono 4 file generation

Progress in 0.1.1: actual PrusaSlicer 2.9.4 → UVTools 7.0.1 conversion and full layer/
parameter readback passed with networking disabled, including a supported 104-layer
fixture. A guarded research CLI is implemented. See `BACKEND_VALIDATION.md`.
Automatic orientation/editable holes/support-point integration remains open, and no
firmware or physical print has been qualified. Encrust profile review is recorded in
`ENCRUST_REVIEW.md`.

- Install/pin qualified PrusaSlicer and UVTools binaries with hashes and source references.
- Probe real CLI versions/formats and create a complete Mono 4 SLA profile.
- Slice closed/asymmetric test fixtures to SL1, convert to PM4N and reopen.
- Compare pixels, axis mapping, settings and Z/layer counts; measure RSS/disk/wall time.
- Implement typed adapters, process runner, cancellation and atomic publication.
- Resolve orientation/hollowing/holes/support-editing API feasibility before promising UI coverage.

Exit: reproducible backend integration tests pass; output is a hardware-test candidate.

## M2 — seamless offline desktop baseline

Desktop progress in 0.2.0: project save/reopen, centered rotation/scale with undo, explicit
settings, support generation, cancellable native slicing, decoded layer preview and
verified calibration-candidate export are wired together. See `DESKTOP_WORKFLOW.md`.
The full M2 feature set remains incomplete: translation/copies, automatic orientation,
hollowing/drain-hole editing, broader platform trials and large-job profiling remain open.

- Editable transforms, undo, copies, supports/hollowing/holes and profile selection.
- Project save/reopen, real sliced-layer preview, meaningful issue review and export.
- Responsive workers, stale-result rejection and recoverable failure paths.
- Package/install trials on Ubuntu 24.04/26.04 and X11/Wayland.
- Run from fresh local state with networking disabled and retain evidence.

Exit: Edwin can select a local STL and obtain a validated PM4N entirely through Seesaw.
This is the first “ready for you to test” milestone, not the current starter.

## M3 — physical Mono 4 qualification

- Record firmware and exact Anycubic clear water-washable resin variant.
- Establish exposure/motion settings with calibration pieces.
- Print an asymmetric scale/orientation fixture before a larger model.
- Print a small representative Thingiverse model; retain its attribution/license locally.
- Record measurements, photos, failures and the final artifact checksum.

Exit: repeatable print evidence supports the Mono 4 compatibility label.

## M4 — expand and compare

- Benchmark mslicer and accept an optional adapter only if correctness and gains justify it.
- Qualify additional resin printer profiles individually.
- Add an FDM route through PrusaSlicer to G-code with separate setup/preview/validation.
- Publish a capability matrix with source-only, integration-tested and hardware-tested levels.

## M5 — local AI orchestration

- Optional image/text-to-3D provider adapters and user-managed weights.
- Per-model CUDA/driver/VRAM/RAM/disk checks with clear minimum/recommended labels.
- Local progress, cancellation, OOM recovery and generated-mesh inspection.
- Keep ordinary slicing independent of AI packages and model licenses.
