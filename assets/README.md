# UniversalTester Assets Directory

This directory stores visual assets for UniversalTester, including application icons, desktop branding, and GUI headers.

## Directory Structure

```text
assets/
├── icons/
│   ├── icon.ico          # Application icon for Windows executable (.exe) and window titlebar
│   ├── icon.png          # High-resolution application icon for Linux (.deb), macOS, and taskbar
│   └── icon_256x256.png  # (Optional) Full-resolution master icon
└── logo/
    ├── logo.png          # Main logo image displayed in the Desktop GUI header and documentation
    └── logo_dark.png     # (Optional) Alternative logo optimized for Dark mode if different
```

## Recommended Image Specifications

| Asset | File Name | Recommended Format & Size | Used For |
| :--- | :--- | :--- | :--- |
| **Main Logo** | `logo/logo.png` | PNG (transparent background), ~256x256 or 512x512 | Desktop GUI header banner & README |
| **App Icon (PNG)** | `icons/icon.png` | PNG (square, transparent), 256x256 or 512x512 | Linux `.deb` launcher, window icon |
| **App Icon (ICO)** | `icons/icon.ico` | Multi-layer ICO (16x16, 32x32, 48x48, 256x256) | Windows `.exe` executable & taskbar |

> **Quick Tip:** If you only have a single `.png` picture, you can place it in `assets/logo/logo.png` or `assets/icons/icon.png`. UniversalTester will automatically detect and load it!
