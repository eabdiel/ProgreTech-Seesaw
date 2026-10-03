# Experimental image-to-3D and local agent connection

Seesaw is [ProgreTech](https://progretech.com)'s open-source offline slicer for
Linux/Ubuntu. The Experimental menu adds optional generation; ordinary slicing
never starts a model, contacts an agent or requires a network connection.

## Available workflows

- **CPU image relief:** a brightness height map on a closed flat base. Adjust width,
  base thickness, relief depth and inversion. This works without CUDA or weights;
  it does not reconstruct the hidden sides of an object.
- **Local 3D reconstruction:** trellis.cpp v0.8.1, pinned Q4 GGUF geometry weights,
  resolution 512 and 12 steps. Each recast uses a new recorded seed. The native
  backend remeshes its output; optional MeshFix repair may alter fine details.
  Seesaw requires a closed positive solid, sets the requested physical width,
  previews the STL and imports it through the normal slicing workflow.
- **OpenClaw prompt intake:** enter a loopback address or HTTPS Tailscale `.ts.net`
  gateway address, your agent ID and token. Send an image and prompt, continue with
  corrections, or start a new conversation. The token stays in memory and a pipe;
  it is not saved in a project or passed in command-line arguments. Redirects and
  environment HTTP proxies are disabled for authenticated agent requests.

The reconstruction model itself is image-conditioned. Text corrections go to your
configured OpenClaw agent; they do not automatically become TRELLIS conditioning.
Preview an agent-produced STL with **Preview generated STL**, or select its revised
image and recast. Automatic remote artifact transfer is not implemented in 0.4.0.
A chat response never grants slicing/export readiness and is never executed as code.

## Setup and requirements

Use **Download local 3D runtime + Q4 weights** for a separate, user-triggered
installation. The application ships a pinned URL/hash manifest, not model weights.
The download is about 4 GB and needs at least 9 GiB free space during installation.
SHA-256 is checked before runtime use. Source/runtime licensing remains separate:
[trellis.cpp](https://github.com/pwilkin/trellis.cpp),
[TRELLIS.2](https://github.com/microsoft/TRELLIS.2), and
[quantized weights](https://huggingface.co/ilintar/trellis2-gguf).
Compatible existing `trellis-cli` and weights folders can instead be entered directly.
This installs a pretrained model; it does not train a new model from scratch.

The tested workstation has an RTX 5060 Ti with 16 GB VRAM and NVIDIA driver 595.91.07.
This is a tested configuration, not a universal minimum. Other GPUs, driver versions
and low-RAM systems are unqualified. Seesaw refuses CPU inference fallback for this
CUDA adapter, monitors the process's GPU allocation and stops at a sampled 12 GiB
limit. Sampling cannot prove the absence of shorter allocation peaks. Model and
CPU geometry processes have deadlines and can be cancelled independently of Qt.
A cooperative GPU lock prevents overlapping Seesaw/factory visual jobs.

For a remote agent, install/configure OpenClaw and Tailscale yourself. Enable the
OpenClaw chat-completions endpoint and use private Tailscale Serve, preserving any
existing routes. Do not expose the operator gateway publicly. The setup panel
links to the official instructions and can save an offline guide. The agent needs
a vision-capable communication model or image-analysis tool, plus separate media
and 3D tools. A language model alone is not a diffusion or reconstruction engine.

## Evidence and limits

On 2026-10-03 two seeds reconstructed a generated robot image on the target RTX.
The first raw export was rejected as open. Native remeshing plus explicit MeshFix
repair produced closed positive-volume meshes. A full Qt worker trial generated,
previewed and imported the resulting 60 mm-wide STL; changing width invalidated
its previous result. CUDA stages took roughly 36–51 seconds in these trials;
additional mesh repair/inspection takes time. This is bounded software evidence,
not broad model-quality or physical-print qualification.

The offline relief path and private HTTP request contract have unit tests and an
actual desktop render/import smoke. The workstation's first text-only Imagen model
failed image intake; the installed vision model correctly identified a test image,
but the full gateway turn hit memory-checkpoint/tool delays. Gateway integration
remains experimental and should be tested with the user's configured agent.

Generated geometry still needs inspection of wall thickness, details, supports,
orientation and material settings. Normal printer-specific export gates remain
in force. No automatic printing or USB-device actuation is added.
