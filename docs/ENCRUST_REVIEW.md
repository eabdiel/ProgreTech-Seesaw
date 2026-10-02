# Encrust profile reference review

Owner-supplied reference: [vvvlladimir/Encrust](https://github.com/vvvlladimir/Encrust).
Reviewed 2026-10-02 at commit `458266d94086bfa84312994c0440a7890d482604`.

The inspected source declares **AGPL-3.0-only**, matching Seesaw's project license.
No Encrust code or profile files have been copied into Seesaw in this review. Any
future reuse must preserve attribution, source revision and its unverified status.

## Findings

- `assets/profiles/printers/` contains **100 TOML printer profiles** at this revision.
- There is a [Photon Mono 4K profile](https://github.com/vvvlladimir/Encrust/blob/458266d94086bfa84312994c0440a7890d482604/assets/profiles/printers/anycubic-photon-mono-4k.toml):
  3840 × 2400, 134.4 × 84 mm, PWMA revision v516. This is not the Mono 4.
- The inspected printer catalogue and Anycubic writer flavour enum do not contain a
  Mono 4/PM4N entry. Keep the already source-reviewed UVTools Mono 4 definition.
- The [water-washable resin preset](https://github.com/vvvlladimir/Encrust/blob/458266d94086bfa84312994c0440a7890d482604/assets/profiles/resins/water-washable.toml)
  explicitly says **UNVERIFIED**. It is generic, not qualification evidence for
  Edwin's Anycubic clear bottle, room temperature or printer.
- [Profile design](https://github.com/vvvlladimir/Encrust/blob/458266d94086bfa84312994c0440a7890d482604/docs/design/profiles.md)
  separates printer, resin and support profiles, uses stable file-stem IDs, keeps
  user overrides separate from shipped profiles and records per-printer resin tuning.
- Printer records express physical display size separately from pixel resolution,
  mirroring, build volume, format/revision and firmware capabilities. These are useful
  fields for Seesaw's future profile catalogue and compatibility matrix.

## Seesaw decision

Retain the PrusaSlicer → SL1 → UVTools baseline. Use Encrust as an additional attributed
reference when building the catalogue/import schema. Do not advertise the entire
catalogue as supported merely because the records can be read. Preserve source,
source revision, unknown/verified flags, firmware capability and calibration evidence
for every imported field.

Suggested mapping:

| Encrust field | Seesaw profile responsibility |
| --- | --- |
| Stable file ID, manufacturer/name | Canonical printer identity, distinct from display name |
| Display pixels/mm, mirror flags | Raster geometry and explicitly tested axis mapping |
| Build volume | Mechanical/printable bounds, separate from illuminated LCD area |
| Output family/extension/revision | Encoder capability and exact format version |
| Firmware flags | Supported per-layer and motion features, not inferred from file suffix |
| Per-printer resin tuning | Material settings tied to printer and layer height |
| UNVERIFIED annotations | Qualification status and visible calibration requirement |

Do not infer “water washable” exposure from the resin category. Keep exact product,
color, temperature and measured results separate. Do not silently replace a missing
Mono 4 record with the similarly named Mono 4K profile.
