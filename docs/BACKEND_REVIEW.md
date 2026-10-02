# Backend review — 2026-10-02

This is source and documentation evidence, not a benchmark or print certificate.
Clones were inspected at the revisions below. No upstream implementation code was
copied into Seesaw. Each claim should be rechecked when updating the backend lock.

| Upstream | Reviewed revision | Release relationship |
| --- | --- | --- |
| PrusaSlicer | `30ef59195e0f3ee6f270b185bb5f9fb5f349f81f` | Development HEAD; latest release API reported `version_2.9.6`, a separate binary candidate |
| UVTools | `e892d3f0c466ce795f0ffffd7365fae9c64d6b78` | Annotated `v7.0.1` tag resolves to this commit |
| mslicer | `e89e4898069e7d207254e5b9c4c0afb72f822dbe` | Development HEAD, not yet selected for packaging |

## PrusaSlicer

- [Repository](https://github.com/prusa3d/PrusaSlicer) and
  [license at reviewed revision](https://github.com/prusa3d/PrusaSlicer/blob/30ef59195e0f3ee6f270b185bb5f9fb5f349f81f/LICENSE).
- [CLI argument parsing](https://github.com/prusa3d/PrusaSlicer/blob/30ef59195e0f3ee6f270b185bb5f9fb5f349f81f/src/slic3r-app-launcher/src/Slic3r/App/Launcher/ReadCLI.cpp)
  exposes `--export-sla` / `--sla`.
- [Action execution](https://github.com/prusa3d/PrusaSlicer/blob/30ef59195e0f3ee6f270b185bb5f9fb5f349f81f/src/slic3r-app-cli/src/Slic3r/App/CLI/ProcessActions.cpp)
  contains SLA slicing/export handling.
- [Configuration definitions](https://github.com/prusa3d/PrusaSlicer/blob/30ef59195e0f3ee6f270b185bb5f9fb5f349f81f/src/slic3r-shared/src/Slic3r/Biz/Config/Legacy/PrintConfig.cpp)
  include display pixels/mirroring, `supports_enable`, `hollowing_enable` and
  `sla_archive_format`. Their existence is not proof that every GUI editing operation
  is available through a stable CLI.
- [Orientation job](https://github.com/prusa3d/PrusaSlicer/blob/30ef59195e0f3ee6f270b185bb5f9fb5f349f81f/src/slic3r/GUI/Jobs/RotoptimizeJob.cpp)
  is GUI-side evidence. Headless integration remains a spike.

Decision: reuse SLA preparation/rasterization. Do not fork the GUI. First prove a
small model can be sliced with a complete non-Prusa SLA profile using a stable binary.

## UVTools

- [Repository](https://github.com/sn4k3/UVtools),
  [v7.0.1 release](https://github.com/sn4k3/UVtools/releases/tag/v7.0.1),
  [license](https://github.com/sn4k3/UVtools/blob/e892d3f0c466ce795f0ffffd7365fae9c64d6b78/LICENSE).
- [AnycubicFile.cs](https://github.com/sn4k3/UVtools/blob/e892d3f0c466ce795f0ffffd7365fae9c64d6b78/UVtools.Core/FileFormats/AnycubicFile.cs)
  registers `pm4n` as Photon Mono 4 (around line 1315) and maps `.pm4n` to
  `PhotonMono4` (around line 1996). Mono 4K uses `pwma`; these are distinct printers.
- [Machine.cs](https://github.com/sn4k3/UVtools/blob/e892d3f0c466ce795f0ffffd7365fae9c64d6b78/UVtools.Core/Printer/Machine.cs)
  lists Mono 4 as 9024 × 5120, 153.408 × 87.040 × 165 mm with horizontal flip.
- [ConvertCommand.cs](https://github.com/sn4k3/UVtools/blob/e892d3f0c466ce795f0ffffd7365fae9c64d6b78/UVtools.Cmd/Symbols/ConvertCommand.cs)
  accepts input, target type/extension and output; offers `--no-overwrite` and resolves
  target encoders. Some error branches return without throwing, so status zero alone
  is insufficient for Seesaw's completion check.
- [PrusaSlicer setup](https://github.com/sn4k3/UVtools/wiki/Setup-PrusaSlicer)
  explicitly instructs users to export SL1, open it in UVTools and convert it.
- [CLI documentation](https://github.com/sn4k3/UVtools/blob/e892d3f0c466ce795f0ffffd7365fae9c64d6b78/README.md)
  lists `convert`, `print-properties`, `print-issues`, `print-machines`, `print-formats`
  and extraction/comparison operations. Use actual CLI probes when implementing adapters.

Decision: use the existing PM4N codec. Confirm native Linux runtime dependencies,
version probe, supported format list and full readback on representative artifacts.
No separate homegrown encoder is justified by this review.

## mslicer

- [Repository](https://github.com/connorslade/mslicer) and
  [GPL-3.0 license](https://github.com/connorslade/mslicer/blob/e89e4898069e7d207254e5b9c4c0afb72f822dbe/LICENSE).
- [Top-level README](https://github.com/connorslade/mslicer/blob/e89e4898069e7d207254e5b9c4c0afb72f822dbe/README.md)
  advertises CTB, GOO, NanoDLP and SVG outputs and Linux builds. It makes performance
  claims that have not been reproduced here; PM4N is not among its listed outputs.
- [Slicer crate README](https://github.com/connorslade/mslicer/blob/e89e4898069e7d207254e5b9c4c0afb72f822dbe/slicer/README.md)
  documents a mesh/transform-oriented CLI; its embedded help says GOO-only output.
  This differs from the top-level description and requires a runtime check.
- [Automatic support code](https://github.com/connorslade/mslicer/blob/e89e4898069e7d207254e5b9c4c0afb72f822dbe/tools/src/supports/auto/mod.rs)
  contains overhang placement and support routing; the tree also includes a supports
  panel and project support storage. Do not infer absence of support generation from
  the README's proprietary-tool recommendation.

Decision: evaluate after the reference pipeline. Benchmark the same supported meshes
and compare layers, physical scale, antialiasing, parameters, memory and conversion
losses through UVTools. Adoption requires demonstrated benefit and correctness; it
must remain optional if it cannot cover the full resin preparation workflow.

## Comparison and reuse policy

| Question | PrusaSlicer | UVTools | mslicer |
| --- | --- | --- | --- |
| Primary role here | Preparation + rasterization | Layer inspection + codec | Alternative rasterization |
| Native language | C++ | C#/.NET | Rust |
| Python integration | Subprocess first | Subprocess first | CLI experiment first |
| PM4N source evidence | Not relied upon | Explicit at v7.0.1 revision | Not in reviewed output list |
| Required baseline | Yes | Yes | No |
| Unresolved | Headless editing operations | Runtime/readback/firmware qualification | Capability and quality/performance qualification |

“Best of all three” means selecting verified strengths, not requiring all three in
every job. Avoid general claims about competitors' logins or internet check-in
policies: they vary by version and are unnecessary to Seesaw's offline contract.
