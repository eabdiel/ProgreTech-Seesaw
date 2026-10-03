# Layer findings and bounded repair (0.3.1)

Failed resin jobs retain inspection layers when encoding/readback succeeded but the
native issue checks found problems. The Layers selector jumps to each recognized
island and shows a magnified crop with a red outline. Inspection never grants export
readiness. Unknown finding formats stay blocked and remain available in job logs.

**Remove isolated single pixels** is off by default and is a project preparation
choice, separate from material calibration. It permits at most 64 native-reported
single-pixel islands per job. UVTools 7.0.1 performs one removal pass; attachment,
morphology, resin-trap filling, suction-cup edits and empty-layer removal are explicitly
disabled. Seesaw then compares every source/repaired raster and requires that exactly
the pre-reported singleton coordinates changed from nonzero to zero. Any other change,
missing removal, count/dimension change, cancellation or unexpected output blocks export.

The repaired SL1 goes through the ordinary PM4N encoding, native metadata and every-layer
readback checks. Native issue detection runs again. Larger islands, new findings and
remaining issues still block export. The manifest records removed pixel coordinates,
count and verification scope; the source STL and original layer archive are retained.
No Python printer codec or custom island-removal algorithm is implemented.

Source: [UVTools 7.0.1 OperationRepairLayers](https://github.com/sn4k3/UVtools/blob/v7.0.1/UVtools.Core/Operations/OperationRepairLayers.cs).
The adapter deliberately overrides upstream defaults; running the general repair operation
with defaults would authorize broader changes than this feature promises.

The project JSON schema advances to version3. Versions1/2 migrate with repair disabled.
The repair choice participates in the job fingerprint and is rejected for filament
printers. Changing it invalidates any previous preview/export result.

Research evidence: the original full-size ctrlV sample, rotated X=35 degrees with native
supports and 0.15 mm layers, produced 285 layers and four one-pixel islands. The bounded
native repair changed exactly those four coordinates and no others across all 285
rasters. The selected post-repair issue checks returned zero. This establishes software
behavior for that fixture; the settings/exposures are synthetic test inputs, not a
recommended resin recipe. It does not establish firmware acceptance or physical printing.

Evidence root: `/mnt/pt-context/job-artifacts/seesaw-profiles-workspace-20261003/`.
See `repair-research/pixel-delta.json`, native operation/settings logs, `findings-ui/`
and `full-sample-repair-result.json`. The integrated worker completed in 239.603 seconds:
285 repaired layers checked, four exact removals, all 285 PM4N readback layers identical
to the repaired archive, expected metadata/exposures/Z, and zero selected final issues.
The result remains a software-validated, physically unqualified calibration candidate.
