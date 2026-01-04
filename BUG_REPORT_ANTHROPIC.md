# Anthropic Support Email
## Claude Chrome Extension Crashes in macOS Split View Mode

**Send to**: [email protected]

---

**Subject**: Claude Chrome Extension Crashes in macOS Split View Mode - Critical Bug

---

Hi Anthropic Support Team,

I'm reporting a critical crash affecting the Claude Chrome extension when used in macOS split view mode on Sequoia.

## Problem Summary
The Claude Chrome extension causes Chrome to crash completely (EXC_BREAKPOINT error) when clicked while Chrome is in macOS split view mode. This makes the extension unusable for users who work in split view, which is a common productivity workflow.

## My Environment
- **Extension**: Claude in Chrome (latest version from https://claude.ai/chrome)
- **Chrome**: 143.0.7499.170 (Official Build) arm64
- **Operating System**: macOS 26.1 Sequoia (25B78)
- **Hardware**: MacBookAir M1 (8GB RAM)
- **Claude Plan**: [Pro/Team/Enterprise]

## Steps to Reproduce
1. Install Claude Chrome extension
2. Open Chrome on macOS Sequoia
3. Enter split view mode:
   - Click green window button on Chrome
   - Select "Tile Window to Left/Right of Screen"
   - Chrome is now in split view with another app
4. Click the Claude extension icon in the toolbar
5. **Chrome crashes immediately**

## Expected vs Actual Behavior
- **Expected**: Extension side panel opens normally
- **Actual**: Chrome crashes completely, all tabs close, work is lost

## Crash Details
```
Exception: EXC_BREAKPOINT (SIGTRAP)
Thread: CrBrowserMain
Location: ChromeMain + 50208788
```

Full crash report attached.

## Root Cause Analysis
After investigation, this appears to be related to a known Chromium bug (#355266358) where the `chrome.sidePanel` API crashes on macOS ARM systems. The split view window configuration on macOS Sequoia triggers this underlying Chromium bug.

## Workaround I'm Using
I have to exit split view mode before using the Claude extension, then re-enter split view after. This is very disruptive to my workflow.

## Impact
This affects anyone who:
- Uses Claude Chrome extension on macOS Sequoia
- Has an Apple Silicon Mac (M1/M2/M3)
- Works in split view mode for productivity

## Questions
1. Is this a known issue on your end?
2. Are you working with the Chromium team on this sidePanel crash bug?
3. Is there any short-term fix planned (like showing a warning or using popup instead of sidePanel in split view)?
4. What's the expected timeline for a fix?

## Suggestions for Short-Term Fix
Until Chromium fixes the sidePanel bug, could the extension:
1. Detect when Chrome is in split view mode
2. Show a notification warning users before opening
3. Or use a popup interface instead of sidePanel when in split view

This would prevent the crash and allow the extension to remain functional.

## Additional Context
I'm also filing this with the Chromium team (issue tracker) and in the claude-code GitHub repository to help get visibility across all teams.

## Attachments
- Full crash report from macOS (DiagnosticReports)
- Detailed technical analysis document

Thank you for looking into this! The Claude extension is fantastic, and I'd love to be able to use it in split view mode without crashes.

Best regards,
[Your Name]
[Your Email]

---

**Note**: Crash report location on Mac:
`~/Library/Logs/DiagnosticReports/Google Chrome_[timestamp].crash`
