# ProgreTech Seesaw

Canonical source: `/home/edwin/PycharmProjects/ProgreTech-Seesaw`.
Canonical product memory project: `ProgreTech-Seesaw`; use your runtime identity.
Follow inherited workstation memory/access policies. Do not consult other roles' private records.

Read `docs/TECHNICAL_SPEC.md`, `docs/BACKEND_REVIEW.md`, `docs/ROADMAP.md` and
`docs/VALIDATION.md` before changing workflow or claiming printer support.

- Isolate work on task branches/worktrees. Preserve unrelated changes.
- Keep source in this repository. Task assets/intermediates go under
  `/mnt/pt-context/job-artifacts/<task-id>/`; final deliverables go under
  `/mnt/pt-context/deliverables/<task-id>/`. Verify the mount with `findmnt -T`.
- Do not confuse Mono 4, Mono 4K and Mono 4 Ultra profiles.
- Keep the baseline offline, Python-driven and free of mandatory CUDA/model dependencies.
- Reuse backend algorithms and codecs. Never claim extension renaming is format conversion.
- A successful unit test is not a firmware/physical-print qualification.
- User meshes, raw logs, generated printer files, credentials and model weights stay out of Git.
- Run `uv run pytest -q` and `uv run ruff check .` for core changes; desktop changes
  also need an actual launch/render/import check with the limits recorded.
- Changes to job readiness must preserve fail-closed export and stale-result rejection.

The owner authorized GitHub repository creation, commits, merges and pushes for this
project. That does not authorize unrelated deployment, messaging or printer actuation.
