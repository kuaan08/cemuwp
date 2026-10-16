# Xbox One UWP: alternative frontend builds

Two independent, installable UWP flavors are available in branch `uwp/d3d11-dual`.

| Actions workflow | Frontend | Graphics implementation | Artifacts |
| --- | --- | --- | --- |
| [Cemu Xbox One - Original UI (D3D12 experimental)](../.github/workflows/cemu-original-ui-uwp.yml) | Original ImGui/Cemu host UI from our PrismFox-based fork | **Original** experimental D3D12/FXC backend; **not** Rodrigo's D3D11 | `cemu-xbox-one-original-ui-d3d12-x64` |
| [Cemu Xbox One Rodrigo D3D11 and experimental D3D12](../.github/workflows/cemu-rodrigo-dual-uwp.yml) | Rodrigo's XAML UWP host | Rodrigo native D3D11 (may use WARP fallback) / separate experimental D3D12 translation | `cemu-xbox-one-d3d11-dual-x64` |

## Original UI workflow

- Compiles **our original frontend and original Cemu D3D12 renderer** from `src/`, including its existing overlay and Xbox-specific graphics test controls; no Rodrigo Cemu/SDL3/host runtime is copied into its build.
- Reuses the previously successful Windows 2022 UWP x64 build route, CMake, vcpkg cache and complete MSIX packaging path.
- Does not download Rodrigo's large `ports/` Git submodules: initializes only the original Cemu dependencies.
- Original UI package is intentionally installed separately: `CemuXboxOneLegacy.Kuaan08` with publisher `CN=CemuXboxOneLegacy`, and distinct `cemu-legacy:` protocol. This prevents overwriting the prior `CemuUWP.Unofficial` installation or the Rodrigo variant.
- Because identities are separate, app-local settings, MLC, saves, and game-library data **are not shared automatically**. Back up saves and install legally owned content as needed.

## How to build

Open Actions on `kuaan08/cemuwp`, choose **Cemu Xbox One - Original UI (D3D12 experimental)**, select branch `uwp/d3d11-dual`, then use **Run workflow**. A source/workflow change to the original frontend can also trigger the job.

The uploaded `cemu-xbox-one-original-ui-d3d12-x64` artifact should contain a complete MSIX plus its matching `.cer` and any x64 dependencies. Set application type to **Game** on the Xbox One Dev Mode portal.

**Compatibility caveat:** In previous Xbox One Fat tests, our D3D12 game rendering still crashed in the Xbox UWP `umd12ddi.dll` driver. This alternative only preserves that frontend and lets us regression-test improvements. Building successfully does **not** show that games boot.

## Bringing Rodrigo's D3D11 into our original UI

This remains **future integration work**, not a selectable feature in the original-UI build. It requires changes to the frontend/render lifecycle, embedded Cemu API, D3D11 swapchain/device ownership, input abstraction, graphics profiles and per-game settings; the two projects cannot switch frontend by simply changing a CMake flag. Preserve the two reliable independent build pipelines as references during the port.

The original branch `uwp/xbox-one` is untouched.
