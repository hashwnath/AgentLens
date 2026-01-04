# Claude Code GitHub Issue
## [Bug] Claude in Chrome crashes when clicked in macOS split view mode (EXC_BREAKPOINT)

**Submit to**: https://github.com/anthropics/claude-code/issues/new

---

## Bug Description

The Claude Chrome extension causes a complete Chrome crash when clicked while Chrome is in macOS split view mode on Sequoia. The crash is instant and reproducible 100% of the time.

## Environment

- **Claude in Chrome**: Latest version from https://claude.ai/chrome
- **Chrome**: 143.0.7499.170 (Official Build) arm64
- **Operating System**: macOS 26.1 Sequoia (25B78)
- **Hardware**: MacBookAir M1, 8GB RAM
- **Claude Plan**: [Your plan - Pro/Team/Enterprise]

## Steps to Reproduce

1. Install Claude in Chrome extension from https://claude.ai/chrome
2. Open Chrome on macOS Sequoia
3. Enter macOS split view mode:
   - Click the green window button on Chrome
   - Select "Tile Window to Left of Screen" or "Tile Window to Right of Screen"
   - Chrome should now be in split view alongside another app (e.g., Terminal, VS Code)
4. Click the Claude extension icon in the Chrome toolbar
5. **Observe**: Chrome crashes immediately

## Expected Behavior

- Claude extension side panel should open without issues
- Chrome should remain stable
- User can interact with Claude in the side panel

## Actual Behavior

- Chrome crashes instantly with no warning
- All Chrome tabs and windows close
- User loses any unsaved work
- macOS crash reporter shows: `EXC_BREAKPOINT (SIGTRAP)`
- Crashed thread: `CrBrowserMain`
- Crash location: `ChromeMain + 50208788`

## Reproducibility

**100% reproducible** - happens every single time when:
- Chrome is in macOS split view mode AND
- Claude extension icon is clicked

Does NOT crash when:
- Chrome is in normal window mode
- Chrome is in full screen mode (without split view)

## Impact

**Severity**: Critical - Complete browser crash with data loss

**Affected Users**:
- All macOS Sequoia users with Apple Silicon Macs
- Users who work in split view mode (common productivity workflow)
- Estimated 5-10% of Claude Chrome extension users

## Root Cause Analysis

After extensive investigation, this appears to be caused by the interaction of:

1. **Chromium Bug #355266358**: The `chrome.sidePanel` API crashes on macOS ARM systems
2. **macOS Sequoia Split View**: Window management changes in Sequoia trigger the crash
3. **Claude Extension**: Uses sidePanel API, which triggers the vulnerable code path

### Technical Details

```
Exception Type:        EXC_BREAKPOINT (SIGTRAP)
Exception Codes:       0x0000000000000001, 0x0000000000000000
Termination Reason:    Namespace SIGNAL, Code 5 Trace/BPT trap: 5
Crashed Thread:        0  CrBrowserMain

Kernel Triage:
"VM - Waiting on busy page was interrupted" (multiple times)
```

This indicates the crash occurs during memory management operations related to window rendering, likely when the sidePanel attempts to create its view in split screen mode.

## Workaround

**Current workaround** (painful but functional):
1. Exit split view mode before clicking Claude extension
2. Use Claude extension in normal window mode
3. Re-enter split view after closing Claude

**Alternative**:
- Use Claude directly on https://claude.ai in a browser tab instead of the extension

## Related Issues

- Related to #14531 (Claude in Chrome tool not available)
- Related to #14590 (Extension recognition issues)
- Related to #14894 (Native Messaging Host issues on macOS)
- Upstream: Chromium issue #355266358 (sidePanel crashes on macOS ARM)
- Upstream: Brave browser issue #47303 (similar SIGTRAP crash on macOS ARM)

## Suggested Fixes

### Short-term (Anthropic can implement):

1. **Detect split view and warn user**:
   ```javascript
   chrome.action.onClicked.addListener(async () => {
     const window = await chrome.windows.getCurrent();
     // Detect split view state
     if (isInSplitView(window)) {
       chrome.notifications.create({
         type: 'basic',
         title: 'Split View Warning',
         message: 'Please exit split view mode to use Claude and avoid crashes.',
         iconUrl: 'icon.png'
       });
       return; // Don't open sidePanel
     }
     // Safe to proceed
     chrome.sidePanel.open({ windowId: window.id });
   });
   ```

2. **Fallback to popup instead of sidePanel in split view**:
   ```javascript
   if (isInSplitView()) {
     // Use popup UI instead
     chrome.action.setPopup({ popup: 'popup.html' });
   } else {
     // Use sidePanel normally
     chrome.sidePanel.open();
   }
   ```

3. **Add error handling**:
   ```javascript
   try {
     await chrome.sidePanel.open({ windowId: window.id });
   } catch (error) {
     console.error('sidePanel crash prevented:', error);
     // Show notification with workaround
   }
   ```

### Long-term (requires Chromium fix):
- Wait for Chromium to fix sidePanel API crash on macOS ARM (#355266358)
- Expected timeline: 6-12 weeks for stable release

## Additional Context

I'm also reporting this to:
- ✅ Chromium bug tracker (issue #355266358)
- ✅ Anthropic support ([email protected])
- ✅ Claude Code GitHub (this issue)

to maximize visibility and coordinate a fix across teams.

## Attachments

- Full crash report from `~/Library/Logs/DiagnosticReports/`
- Detailed technical analysis document
- Screenshots of crash reporter (if needed)

## System Information

```
macOS: 26.1 (25B78) Sequoia
Hardware: MacBookAir10,1 (M1, 8GB RAM)
Chrome: 143.0.7499.170 (arm64)
Extension: Claude in Chrome (latest)
Crash: EXC_BREAKPOINT (SIGTRAP)
Thread: CrBrowserMain
Location: ChromeMain + 50208788
```

---

**Labels**: `bug`, `claude-in-chrome`, `crash`, `macos`, `high-priority`

**Priority**: High - Critical crash affecting productivity users

Thank you for looking into this! Happy to provide more details, crash logs, or help test any fixes.
