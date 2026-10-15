# Xbox One Cemu D3D11 / D3D12 test port

This branch is a **separate build variant** based on the full pinned
[Rodrigo Cemu](https://github.com/rodrigoandrigo/Cemu/tree/build-msvc-d3d11)
and [Cemu UWP Host](https://github.com/rodrigoandrigo/Cemu-UWP-Host) sources.
It retains the current experimental PrismFox-style D3D12 port, shader
experiments and texture/DRED diagnostics separately in `uwp/xbox-one`.

## Sources

- Cemu embedded runtime: `c70bca6f94c94dc7fc8e5bdda5e55d85c500f371`
- UWP Host: `7dbfb6aa8716593cf7caed3cbcd39b07aee58c2e`
- SDL3 UWP: `37ee4ec4f4427e45dab91d1b40a5d075cb7ae255`

Pinned Git submodules are in `ports/`. The workflow checks them out
recursively and runs `tools/patch_rodrigo_host.py` to apply modifications
to the host. The original Rodrigo code is not silently rewritten.

## Real functionality

- Full embedded Cemu engine and native D3D11 backend, not just the launcher.
- Native D3D12 translation layer from **Rodrigo** also compiled. Added a
  selector in Settings: D3D11 (default), D3D12 (experimental); restart the
  app after changing the selection.
- Hardware or WARP status and D3D11 Feature Level are read through the DXGI
  device and shown next to the library's renderer status, along with vendor ID.
- All baseline Rodrigo UWP features retained: game library, updates, DLC,
  controller support, shader cache, Graphic Packs and per-game scaling using
  the supported Graphic Pack presets.
- The original FXC/SM5.1 PrismFox D3D12 profile, pipeline scheduling choices
  and resource/depth/DRED A/B experiments remain on `uwp/xbox-one`; those
  are backend-specific and have not been transplanted into the Rodrigo
  renderer under misleading control labels.

## Performance investigation

The user reports that the original Xbox One Fat opened a Wii U game with
Rodrigo's Cemu at 5–7 FPS, while an overlay showed 0 VRAM usage.
The upstream host requests D3D11 FL11.0 and falls back to WARP if native
device creation fails. **VRAM=0 alone does not prove WARP.** This variant
displays a hardware/WARP adapter classification so that the next test can
distinguish software-rendering overhead from other performance bottlenecks.
The UWP host is primarily validated upstream on Xbox Series S, not One Fat.

## Build and test

Use Actions -> `Cemu Xbox One Rodrigo D3D11 and experimental D3D12` for
the `uwp/d3d11-dual` branch. A successful build should upload
`cemu-xbox-one-d3d11-dual-x64`, with a signed development package
and its corresponding test certificate. A CI success **does not**
establish hardware compatibility or gameplay FPS.

Test the same game twice with D3D11: once to warm caches and once warm;
record adapter name, hardware/WARP, feature level, FPS, RAM, VRAM and
which shader effects render. Only then test D3D12 separately if desired.
Do not send personal saves or keys with diagnostic logs.

## Future integration

The two source trees have different embedded hosting architectures.
Merging Rodrigo's CemuEmbed D3D11 renderer into our direct ImGui/D3D12
frontend as a single switch will require adapting lifecycle, texture
formats, shader pipelines, swapchain ownership and settings. This
branch builds the actual Rodrigo Cemu as the working baseline before
attempting a risky cross-architecture merge.
