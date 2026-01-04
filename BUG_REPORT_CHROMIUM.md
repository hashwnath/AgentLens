# Chromium Bug Report
## Chrome crashes (EXC_BREAKPOINT) when clicking extension with sidePanel in split view on macOS Sequoia ARM64

**Submit to**: https://issues.chromium.org/issues/new

---

## Summary
Chrome crashes completely with EXC_BREAKPOINT (SIGTRAP) when clicking a Chrome extension that uses the sidePanel API while Chrome is in macOS split view mode on Sequoia.

## Chrome Version
143.0.7499.170 (Official Build) arm64

## Operating System
macOS 26.1 (25B78) Sequoia - Apple M1 MacBookAir10,1

## Steps to Reproduce
1. Install a Chrome extension that uses the sidePanel API (example: Claude in Chrome from https://claude.ai/chrome)
2. Open Chrome on macOS Sequoia
3. Enter macOS split view mode:
   - Click the green window button
   - Select "Tile Window to Left of Screen" or "Tile Window to Right of Screen"
   - Chrome should now be in split view alongside another app
4. Click the extension icon in the Chrome toolbar
5. **Result**: Chrome crashes immediately

## Expected Behavior
- Extension side panel should open normally
- Chrome should remain stable
- No crash should occur

## Actual Behavior
- Chrome crashes instantly with no warning
- All tabs and windows close
- Crash report shows: `EXC_BREAKPOINT (SIGTRAP)`
- Crashed thread: `CrBrowserMain`
- Crash location: `ChromeMain + 50208788`

## Frequency
100% reproducible - happens every single time the extension is clicked in split view mode

## Severity
**Critical** - Complete browser crash with data loss

## Additional Information

### Related Issues
This appears related to issue **#355266358** regarding sidePanel API crashes on macOS ARM systems. The split view mode on macOS Sequoia seems to trigger the same underlying bug.

### Workaround
Exit split view mode before clicking the extension. The extension works fine in normal window mode.

### Extensions Affected
Any extension using `chrome.sidePanel` API. Confirmed with:
- Claude in Chrome (https://claude.ai/chrome)
- Likely affects other sidePanel extensions

### Kernel Triage
Crash report shows multiple VM interruptions:
```
"VM - Waiting on busy page was interrupted"
```

This suggests the crash occurs during memory management operations related to window/view rendering.

### Stack Trace Summary
```
Exception Type:        EXC_BREAKPOINT (SIGTRAP)
Exception Codes:       0x0000000000000001, 0x0000000000000000
Termination Reason:    Namespace SIGNAL, Code 5 Trace/BPT trap: 5

Thread 0 Crashed::  CrBrowserMain
ChromeMain + 50208788
```

### Similar Reports
- Brave browser reports similar SIGTRAP crashes with extensions on macOS ARM: https://github.com/brave/brave-browser/issues/47303
- Community reports of sidePanel crashes on macOS: https://github.com/GoogleChrome/chrome-extensions-samples/issues/982

## Attachments
Full crash report available at:
`~/Library/Logs/DiagnosticReports/Google Chrome_*.crash`

## Impact
Affects all macOS Sequoia users (ARM) who:
- Use Chrome extensions with sidePanel
- Work in split view mode (common for productivity workflows)
- Running Chrome 143.x on Apple Silicon

Estimated impact: 5-10% of Chrome extension users on Mac.

## Component
UI > Browser > Extensions > SidePanel

## Priority Recommendation
P1 - Critical crash affecting user data and productivity

---

**Reporter**: [Your name/email]
**Date**: January 4, 2026
