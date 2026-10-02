# Mono 4 backend integration — 2026-10-02

Release 0.1.1 adds a research CLI pipeline. The desktop remains a foundation preview;
its printer export button is disabled. These checks do not qualify printer firmware
or Edwin's Anycubic clear water-washable resin exposure settings.

## Actual runtimes and findings

- Ubuntu's `prusa-slicer` package **2.9.4+dfsg-4**, executable reports
  `PrusaSlicer-2.9.4+UNKNOWN`. This replaces 2.9.6 as the first *tested* candidate.
- Upstream UVTools package **7.0.1**, downloaded release asset SHA-256 verified against
  GitHub. Use `/usr/lib/uvtools/UVtoolsCmd`: the Ubuntu wrapper `uvtools --cmd` did not
  reliably emit output for all probes. `--core-version` reports 7.0.1; the command-line
  assembly's own `--version` reports 2.2.0 plus its commit. Do not conflate them.
- UVTools ships an explicit `Anycubic Photon Mono 4.ini` profile, including the expected
  raster, display size, mirroring and PM4N marker. The research adapter generates an
  allowlisted standalone configuration from numeric settings, avoiding imported scripts.
- SL1's `numFade` becomes UVTools' bottom-layer count. A zero fade count produced zero
  bottom layers in an early test; the adapter now requires and verifies a positive count.
- Motion parameters exposed by UVTools use mm/min, while PM4N's native header stores
  mm/s. A requested 120 mm/min was decoded as 120 through the normalized API and stored
  as 2 in the native header. Keep those units explicit.
- The PM4N PW0 raster codec preserves the high nibble and expands it on decode:
  `expected = (input >> 4) * 17`. Every pixel is checked against this exact mapping.

## Integration evidence

Original test geometry is an asymmetric L-shaped, watertight mesh built by
`tools/qualify_pipeline.py`. No downloaded or third-party model is required.

| Probe | Result |
| --- | --- |
| Flat 0.5 mm fixture, 0.05 mm layers, antialiasing on | 10 layers; metadata and exact quantized pixels passed; no selected UVTools issues |
| Same solid pipeline with networking disabled | Passed, 10 layers; same output checksum as network-enabled run |
| Flat elevated supported fixture | Rejected: UVTools reported the abrupt unsupported-area growth as an island |
| Fixture rotated 35° around X, supported, 0.1 mm layers, antialiasing on | Pixel/metadata checks passed, but rejected for one 1-pixel island finding |
| Rotated supported fixture, antialiasing off, networking disabled | Passed: 104 layers, pixel-identical readback, no selected UVTools issues; ~40 s on development host |

The earlier horizontal fixture had support-pixel overlap, so “island” here is the
upstream detector's support-area/overhang heuristic, not proof of completely disconnected
geometry. Seesaw did not suppress or silently ignore either finding. PrusaSlicer's
documented `gamma_correction = 0` produces binary layers; this is the initial default.
Antialiasing is optional and still checked.

Offline tests ran in a separate Linux network namespace with `unshare --net`, under
the normal user identity, with the installed backend executables and local models.
The installed desktop's STL import/render smoke also passed with networking disabled.

## What the adapter verifies

- Version-qualified executables and a new, isolated job directory.
- Closed input geometry and unrotated build-volume fit; basic RAM/disk preflight.
- Complete SL1 output, native PM4N output and decoded printer identity.
- Raster/display dimensions, layer height/count, bottom/transition counts, exposure,
  waits and lift/retract values with explicit units.
- Every layer's Z coordinate and exposure; monotonic expected layer sequence.
- Every layer's pixels after PM4N → SL1 readback, accounting only for the exact codec
  quantization. No extra rotation or mirroring may be introduced during conversion.
- UVTools island, touching-boundary, print-height and empty-layer checks.
- Native output remains hidden as `.pending.pm4n` until validation succeeds. A failed
  job removes the candidate, preserves diagnostic logs and records a failed manifest.
- Cancellation, nonzero process exits and deadlines stop the process group. A backend
  status of zero is insufficient: a PrusaSlicer low-elevation failure returned zero
  without writing SL1 during development, and is now detected as failure.

The manifest marks `hardware_qualified: false` even on success. Hollow/closed-void
analysis is not claimed: hollowing is disabled in this adapter. The research limit is
512 layers with conservative free-memory checks until large-job behavior is measured.

## Run the repeatable probe

Install the exact backend versions above separately; they are not bundled in Seesaw's
installer. The desktop works without them. In a development checkout:

```bash
uv run python tools/qualify_pipeline.py --output /path/to/new/solid-job
uv run python tools/qualify_pipeline.py --output /path/to/new/supported-job --supports
```

The script's 2.5 s / 25 s exposures are **test values only**, not a recommended resin
preset. Production settings still need calibration. The installed research CLI requires
explicit exposure input:

```bash
progretech-seesaw-cli validate-pipeline /path/to/model.stl \
  --job-dir /path/to/new/job \
  --exposure-seconds 2.5 --bottom-exposure-seconds 25
```

The resulting candidate is diagnostic output, not a firmware-qualified print file.
There is no automatic printer actuation or USB copy. Do not use an arbitrary Thingiverse
model as the first hardware validation; qualify exposure and asymmetric orientation first.

## Remaining preparation/UI work

Wire workers into the desktop, implement saved projects/editable transforms, real layer
preview and reviewed export. The CLI supports manual rotation via prepared input geometry;
automatic orientation and editable support points/drain holes need a proper PrusaSlicer
project/helper interface. Hollowing and resin-trap checks must be qualified before
offering a hollowed-model path. Physical Mono 4 orientation and exposure remain untested.

Encrust is now an additional profile-design reference; see `ENCRUST_REVIEW.md`. Its
Mono 4K profile is not substituted for Mono 4 and its generic resin settings are not
treated as calibration evidence.
