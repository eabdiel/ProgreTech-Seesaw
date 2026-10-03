# Seesaw 0.3 workspace

## Use

1. Select **Anycubic Photon Mono 4** or **Original Prusa i3 MK3S/MK3S+ (0.4 mm)**.
   Resin printers show resins; filament printers show filament profiles.
2. Add a closed STL, or click **Load test file**. The bundled, unchanged
   `ctrlV_3D_test.stl` is ctrlV's Thingiverse 704409 test (50 × 50 × 14.001 mm).
   It was designed as a demanding filament test, not a resin exposure calibration.
   Its supplied CC Attribution–No Derivatives license and original README are included;
   the supplied archive does not state a license version. Its license is separate
   from the application code's AGPL license.
3. Choose a material. Anycubic clear water-washable resin starts without exposure
   settings: enter your own validated values. **Save profile** stores the current
   settings locally; **Import profile** validates and previews a Seesaw material JSON.
   Names do not certify calibration. Exact product SKU and print evidence remain unknown.
4. Use Move X/Y (bed-center coordinates), uniform Scale and Rotate X/Y/Z, then
   **Apply transform**. Choose an instance in the model list. Duplicate, Remove and
   Arrange operate on independent placements of the same source STL. Undo changes
   the project revision. The original file is never overwritten.
5. Choose layer height and material parameters, enable **Generate supports** if needed,
   then **Slice and validate**. Native PrusaSlicer generates supports/raft. Review
   them in actual sliced layers; the preparation viewport shows input geometry.
6. Review Layers, including first/last and overhang regions. Export the calibration
   candidate to a local path or mounted USB drive. The copied file is checksum-verified.
   Safely eject it through Ubuntu. Seesaw sends no commands to a physical printer.
7. Save a `.seesaw` project to retain the source hash, instances, printer revision,
   effective settings and material snapshot. Keep the referenced STL in place.

The in-app Help works offline. Water-washable resin still requires manufacturer-directed
handling and waste disposal; it must not be represented as safe to pour down a drain.

## Capability matrix

| Profile | Native route | Software evidence | Physical evidence |
| --- | --- | --- | --- |
| Photon Mono 4 | PrusaSlicer 2.9.4 → SL1 → UVTools 7.0.1 → PM4N | Offline UI slicing, native settings/Z/pixel readback, placed copies and supports | Not yet tested on firmware/printer |
| MK3S/MK3S+, 0.4 mm | PrusaSlicer 2.9.4 → G-code | Offline UI slicing, body toolpath bounds, actual layer preview, settings/heating readback, supports and verified export | Not yet tested on firmware/printer |

Mono 4 dimensions derive from UVTools' reviewed machine table: 153.408 × 87.04 ×
165 mm, raster 9024 × 5120. MK3S profile settings are flattened from installed
PrusaResearch.ini config_version 2.4.0, Original Prusa i3 MK3S & MK3S+ and Generic PLA.
Packaged JSON retains native start/end sequences; user profiles cannot supply executable
G-code or post-processing. Printer and source notices are under `seesaw/assets`.

FDM layer height, nozzle/bed Celsius, infill percent, speed mm/s and support generation
are editable. The first and ordinary layer temperatures use the selected values.
This initial material adapter is PLA-based; renaming a profile does not turn it into a
qualified ABS/PETG printer configuration. Additional printer definitions need a matching
adapter and tests; arbitrary unverified printer imports are intentionally unavailable.

## Current limits

- One source STL, up to 32 instances; independent files are not yet a multi-model scene.
- XY placement, uniform scale and rotation are supported. Z translation is rejected;
  native resin supports provide elevation. Arrange uses conservative bounding rectangles.
- Hollow/drain editing and automatic orientation are not enabled. Native research
  results are in `HOLLOWING_RESEARCH.md`; they are not an arbitrary-geometry guarantee.
- Resin: at most 512 estimated layers plus conservative RAM admission, then full native
  output checks. FDM: 5000 layers, 2 million extrusion segments, under 256 MiB output.
- Any input change invalidates export; a reopened project must be sliced again.
- Native engines are separate installation prerequisites. This is not yet a complete
  offline installation bundle for a fresh machine. Ubuntu 26.04.1 X11/XWayland is the
  observed platform; 24.04 and native Wayland remain unqualified.
- Settings/readback and layer checks cannot prove adhesion, drainage, cure, mechanical
  safety or firmware acceptance. Edwin's physical calibration is still required.

## Reproducible validation

`tools/smoke_workspace.py` drives actual desktop import, printer/material selection,
profile saving, placement/copies, project reopening, native slicing, actual layer
preview, hash-verified export and printer-change invalidation. `--full-size` preserves
original sample dimensions and uses one instance. `--supports` exercises native supports.
Run in a network-disabled namespace with an available X display. Test exposure values
are synthetic inputs, never resin recommendations. `tools/smoke_workflow.py` also covers
legacy resin workflow, cancellation and supported asymmetric geometry.

Artifacts for this milestone are stored outside Git at
`/mnt/pt-context/job-artifacts/seesaw-profiles-workspace-20261003/`.
See the release evidence manifest for exact checks and package provenance.
