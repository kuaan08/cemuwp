#!/usr/bin/env python3
"""Apply Xbox One diagnostic and selectable renderer UI to pinned Rodrigo UWP host.

Expected upstream: rodrigoandrigo/Cemu-UWP-Host @ 7dbfb6aa.
Fail rather than silently build a host with unpatched or broken controls.
"""
from pathlib import Path
import sys
host = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("ports/Cemu-UWP-Host")

def change(path, old, new):
    p = host / path
    src = p.read_text(encoding="utf-8-sig")
    n = src.count(old)
    if n != 1:
        raise RuntimeError(f"Upstream changed: {p}: expected one occurrence, got {n}: {old[:95]}")
    p.write_text(src.replace(old, new), encoding="utf-8")
    print("PATCHED", p)

change("DirectXPage.xaml",
       '<TextBlock Text="Direct3D 11 is the fixed graphics backend for the UWP host."',
       '<TextBlock Text="D3D11 is the default; D3D12 is experimental. Restart after changing renderer."')
change("DirectXPage.xaml",
       '<TextBlock Text="Graphics API: Direct3D 11" Style="{StaticResource HelpfulTextStyle}"/>',
       '<ComboBox x:Name="graphicsBackendBox" Header="Renderer (restart required)" SelectedIndex="0" SelectionChanged="SettingsSelectionChanged"><ComboBoxItem Content="Direct3D 11 (compatible)"/><ComboBoxItem Content="Direct3D 12 (experimental)"/></ComboBox>')

change("DirectXPage.xaml.cpp",
       '#include <windows.ui.xaml.media.dxinterop.h>',
       '#include <windows.ui.xaml.media.dxinterop.h>\n#include <dxgi.h>')

change("DirectXPage.xaml.cpp",
       '''\t// The UWP host exposes one supported graphics path. Normalize settings from
\t// older builds so an unsupported saved value cannot remain active.
\tif (settings.graphics_api != 3)
\t{
\t\tsettings.graphics_api = 3;
\t\tm_main->SetSettings(settings);
\t}
\trendererMetricsText->Text = "Renderer         D3D11";''',
       '''\t// Use the graphics API selection implemented in the CemuEmbed ABI.
\t// Preserve D3D11 by default. Rodrigo's own D3D12 path remains experimental.
\tselect(graphicsBackendBox, settings.graphics_api == 4 ? 1 : 0, 1);
\tstd::ostringstream gpuInfo;
\tgpuInfo << "Renderer " << (settings.graphics_api == 4 ? "D3D12 EXP" : "D3D11");
\tif (m_deviceResources && m_deviceResources->GetD3DDevice())
\t{
\t\tauto* nativeDevice = m_deviceResources->GetD3DDevice();
\t\tconst auto level = nativeDevice->GetFeatureLevel();
\t\tgpuInfo << " FL " << (level == D3D_FEATURE_LEVEL_11_0 ? "11.0" :
\t\t\tlevel == D3D_FEATURE_LEVEL_10_1 ? "10.1" : "10.0");
\t\tMicrosoft::WRL::ComPtr<IDXGIDevice> dxgi;
\t\tif (SUCCEEDED(nativeDevice->QueryInterface(IID_PPV_ARGS(dxgi.GetAddressOf()))))
\t\t{
\t\t\tMicrosoft::WRL::ComPtr<IDXGIAdapter> adapter;
\t\t\tif (SUCCEEDED(dxgi->GetAdapter(adapter.GetAddressOf())))
\t\t\t{
\t\t\t\tDXGI_ADAPTER_DESC info{};
\t\t\t\tif (SUCCEEDED(adapter->GetDesc(&info)))
\t\t\t\t{
\t\t\t\t\tbool warp = info.VendorId == 0x1414;
\t\t\t\t\tgpuInfo << (warp ? " WARP/SOFTWARE" : " HARDWARE");
\t\t\t\t\tgpuInfo << " vendor 0x" << std::hex << info.VendorId;
\t\t\t\t\tif (warp)
\t\t\t\t\t\tAppendError("XB1-GPU: Microsoft WARP software renderer selected. Low FPS may reflect CPU rendering. VRAM=0 alone does not prove WARP.");
\t\t\t\t}
\t\t\t}
\t\t}
\t}
\trendererMetricsText->Text = FromUtf8(gpuInfo.str());''')

change("DirectXPage.xaml.cpp",
       '\tsettings.graphics_api = 3;\n\tsettings.vsync = vsyncBox->SelectedIndex;',
       '\tsettings.graphics_api = graphicsBackendBox->SelectedIndex == 1 ? 4 : 3;\n\tsettings.vsync = vsyncBox->SelectedIndex;')

# Separate package identity: do not overwrite Rodrigo's original installation,
# saves, imported games or trusted signing identity on an Xbox developer console.
change("Package.appxmanifest",
       'Name="9603d93f-a7c7-491d-9d0b-1a0930897231"',
       'Name="CemuXboxOneDual.Kuaan08"')
change("Package.appxmanifest",
       'Publisher="CN=rodri"',
       'Publisher="CN=CemuXboxOneDual"')
change("Package.appxmanifest",
       'PhoneProductId="9603d93f-a7c7-491d-9d0b-1a0930897231"',
       'PhoneProductId="18a2a39a-74b1-4270-907b-a091970a6b34"')
change("Package.appxmanifest",
       '<DisplayName>Cemu_UWP_Host</DisplayName>',
       '<DisplayName>Cemu Xbox One Dual</DisplayName>')
change("Package.appxmanifest",
       '<PublisherDisplayName>rodri</PublisherDisplayName>',
       '<PublisherDisplayName>Cemu Xbox One Community</PublisherDisplayName>')
change("Package.appxmanifest",
       'DisplayName="Cemu_UWP_Host"',
       'DisplayName="Cemu Xbox One Dual"')

print("Xbox One: selectable D3D11/D3D12 + hardware/WARP diagnostics overlay ready.")
