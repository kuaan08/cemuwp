# Cemu UWP — Xbox One (2013) experimental port

This is an **experimental** Xbox One / Xbox One S / Xbox One X compatibility branch of the unofficial [PrismFox67 Cemu-UWP D3D12 fork](https://github.com/PrismFox67/Cemu-UWP/tree/d3d12-backend).

**Status:** UWP launcher was reported working on the original Xbox One, but launching a game closed the app. The cause has not yet been verified. A successful CI build is not proof that games run.

## Branch

- Source: `PrismFox67/Cemu-UWP`, commit `8a59ff7a2fe77cdb09aff2a4440249cf23e29e81`
- Test branch: `uwp/xbox-one`
- Target: original Xbox One 2013, UWP Dev Mode, x64 package, **App type: Game**
- Not intended for Xbox retail mode.

## First experimental changes

- Prefer the FXC / DirectX bytecode / Shader Model 5.1 compiler on each UWP launch. This overwrites a previously saved DXC choice at startup. DXC can still be selected from Graphics after startup as an experimental alternative.
- Disable frame interpolation at startup; it adds unnecessary work on a 60 Hz / low-power test console.
- Add precise logs at title preparation, launcher-swap-chain release, renderer startup, and PowerPC title launch. Log GPU shader model, binding tier and memory usage before launching.
- Preserve the original D3D12 renderer, input system and UWP app identity for compatibility with existing installations.
- Dedicated GitHub Actions package builder for UWP x64 MSIX and its required dependencies, with vcpkg caching.

## Build

Use [Xbox One UWP workflow](../.github/workflows/xbox-one-uwp.yml) and download the `cemu-xbox-one-uwp-x64` build artifact when successful.

The ZIP is expected to include `.msix`, `Microsoft.VCLibs.x64.14.00.appx` dependency if the Visual Studio SDK generates it, and a temporary `.cer` certificate. Only a successful completed run confirms that those files exist.

## Install and test

1. Xbox One: enable Developer Mode and open Dev Home.
2. From your Windows PC open Xbox Device Portal at `https://<console-ip>:11443`.
3. Add the .msix and its x64 VCLibs dependency from the build ZIP.
4. In Dev Home, select Cemu UWP > View details > set **App type: Game**.
5. Start the app, then try a small self-contained Wii U homebrew RPX before trying a demanding commercial game.
6. If it closes: Xbox Device Portal > File explorer > LocalAppData > `CemuUWP.Unofficial_*` > LocalState > export `log.txt` and `log_previous.txt`. If no log is present, record whether the app crashed while launching the title or during GPU initialization.

## Next compatibility investigations

- Determine whether a failed title is due to shader compilation, UWP executable-memory restrictions, GPU feature support or process memory budget using logs.
- If D3D12 reports unsupported features, implement individual feature-level fallbacks rather than lowering hardware checks without validating shader / pipeline compatibility.
- Profile performance and shader creation on Xbox One before adding rendering optimizations or low-resolution graphic-pack presets.

No paid game files, firmware, keys, or copyrighted game assets are included.

## Xbox One: SM5.1-only configuration

This branch disables SM6/DXC/DXIL at runtime for UWP. The renderer stops probing Shader Model 6+, the shader compiler enforces the FXC/DXBC path, and UI DXC selections are hidden. Saved settings from Series builds are reset to FXC when the UWP frontend initializes. Three FXC pipeline scheduling profiles remain to test accuracy, balanced, and asynchronous operation.

DXC-related source code is intentionally retained for non-UWP builds and upstream merges, but it is not selected or loaded by this Xbox One UWP build. This does not remove the D3D12 GPU requirements or establish game compatibility.

## NES Remix Pack crash investigation (Xbox One Fat)

User-provided `log.txt` and `log_previous.txt` from version `10b4fef` both show `0xc0000005` in `umd12ddi.dll+0x3732d`, immediately after the first color/depth texture format logs; the PPC recompiler, renderer device setup, DXBC FXC, startup command-list submissions and XAudio2 initialize normally. The last memory report was 2035 of 5120 MiB, so an ordinary budget-exceeded termination is not established. The same UMD offset was recorded in an Eden Xbox One experiment with A Short Hike; no single D3D12 call is yet confirmed as responsible.

This diagnostic patch adds `XB1-TEX`, `XB1-RTV`, `XB1-DSV` and `XB1-FBO` BEGIN/END breadcrumbs, bounded to the first few attachments. It also selects non-array TEXTURE2D render-target/depth-stencil view dimensions for native 2D single-slice resources. That view-dimension change is a compatibility experiment, **not a confirmed fix**. Other platforms retain their existing descriptor path.

On the Xbox, launch the same title. If it closes, export only `LocalState/log.txt` and `log_previous.txt` via Device Portal, not the full package data archive; user archives may include private `keys.txt`. Compare the final unmatched BEGIN probe to isolate the next failing D3D12 driver call.

## Second NES Remix test: 538b298

Two logs of commit 538b298 (one with async compile enabled, one disabled) consistently crashed in SraKmd `umd12ddi.dll+0x3732d`. The first color texture and depth resource were each successfully allocated via `CreateCommittedResource` (HRESULT S_OK), but none of the view/FBO trace entry markers appeared.

In `LatteTextureD3D12`, the immediate next call after the successful depth allocation is `D3D12_Checkpoint` which queries `ID3D12Device::GetDeviceRemovedReason()`. This is a **hypothesis, not a proven stack-frame attribution** (native symbols are still required). The next experimental revision skips only this per-allocation query on UWP, preserving other device-removed checkpoints. It logs the constructor exit and brackets texture-view construction. If the crash persists with the new trace, the last completed `XB1-*` record locates the next investigation point.

Do not report the defect as corrected until a real Xbox One game boot survives.
