# Native hollowing and drain-hole research

Research after release 0.2.0, 2026-10-03. This does not enable hollowing or drain
editing in the installed UI. Native PrusaSlicer 2.9.4 provides a demonstrated
headless route through its own 3MF metadata and SLA exporter.

Sources inspected at tag `version_2.9.4`, commit
`69c8e569410efe82259e706cd09a05ea82da9359`:
`src/libslic3r/Format/3mf.cpp`, `src/libslic3r/SLA/Hollowing.cpp` and `.hpp`.
The serializer stores eight drain-hole numbers: position, direction, radius and
height. Its compatibility importer adds the normalized direction to position and
subtracts 1 mm from height. `DrainHole::to_mesh` extends the cylinder along its
normal; that direction points into the model for a surface-origin drain.

A metadata round-trip preserved drain and manual support records through the
native exporter. The subsequent controller-authored raster experiment reused a
native-exported closed 10 mm cube 3MF; no custom mesh XML was constructed. Object
coordinates were -5..5 with build Z translation 5. Explicit CLI centering at
`76.704,43.52` was necessary for the Mono 4 bed. Without it the object straddled
the boundary, and PrusaSlicer returned zero with no archive. Always check output
existence and layer count, not just exit status.

Three offline slices used 0.2 mm layers, no supports, and the existing generated
Mono 4 raster profile. Hollow variants enabled minimum thickness 2, quality 0.5,
and closing distance 0.5. Exposure numbers were synthetic inputs, not a resin
recommendation. Each successful slice produced 50 native 9024 × 5120 layers;
images were inspected individually, excluding thumbnails.

| Observation | Solid | Hollow | Corrected bottom drain |
| --- | ---: | ---: | ---: |
| First layer nonzero pixels | 345744 | 345744 | 334880 |
| Middle layer nonzero pixels | 345744 | 224328 | 224328 |
| First layer center | 255 | 255 | 0 |
| Middle layer center | 255 | 0 | 0 |

An initial outward-pointing record made a blind bottom pocket: layers 5–9 remained
solid between the opening and cavity. This negative fixture matters: a visible
opening alone does not prove drainage. The corrected inward-pointing record was:

```text
drain_holes_format_version=1
object_id=1|0 0 -6 0 0 1 1 6
```

Stored in `Metadata/Slic3r_PE_sla_drain_holes.txt`, this yielded an unexposed center
continuously from the first through the middle layer. The first ten layers each
removed 10864 pixels relative to hollow-only. This establishes a connected raster
opening for this fixture, not physical fluid flow or general mesh correctness.

Pending: typed hole coordinates and transform/undo/persistence semantics;
side/top/rotated-hole fixtures; cavity/drain issue review; hollow-job PM4N roundtrip;
guarded UI; physical resin/firmware qualification. Automatic orientation remains
a separate question; no CLI flag does not prove native headless integration impossible.

Evidence root: `/mnt/pt-context/job-artifacts/seesaw-factory-soak-20261002/`.
`backend-research/controller-raster-6e2bq6ep/` contains solid/hollow/failed-drain
results and the exact script used. `controller-raster-8kta9ynx/` contains the
corrected drain result, with script `backend-research/controller_raster_probe.py`.
Each folder retains native logs, inputs/config and archives. The metadata transit
probe was a reviewed Mak contribution. Codex wrote and checked the raster probe
after rejecting the worker draft; no local-worker raster completion is claimed.

## PM4N readback and cavity checks

A subsequent network-disabled UVTools core 7.0.1 experiment encoded both hollow
variants to PM4N, checked the Mono 4 metadata, decoded back to SL1 and compared all
50 native layer rasters. Both had zero changed pixels. Resin-trap and suction-cup
detection reported one ResinTrap for the closed hollow fixture (layers 10–39),
and zero issues in that selected check set for the corrected bottom-drained
fixture. This is software evidence for these fixtures, not physical qualification
or a guarantee against every geometry/printing issue. Per-layer exposure/Z checks
were not repeated in this research probe; metadata checks and exact raster
comparison are the specific claims here.

Evidence: `backend-research/hollow-readback-sny_x0jh/result.json`, native logs and
readback archives under the same task root; controller script `hollow_roundtrip.py`.
Research PM4N artifacts use synthetic exposures and are not offered as print-ready
files or final deliverables. Installed application behavior is unchanged.
