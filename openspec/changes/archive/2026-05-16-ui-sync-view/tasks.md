## 1. HTML Structure

- [x] 1.1 Add sync mode section to `ui/index.html` with bordered frame and centered status text element
- [x] 1.2 Add sync action group to footer with a single "Sync" button (no prev/next)

## 2. CSS Styling

- [x] 2.1 Add sync mode styles — reuse stylus frame border/padding/sizing via grouped selector or shared properties
- [x] 2.2 Add sync status text styles — DM Mono 1.4rem, centered vertically and horizontally in the frame

## 3. JavaScript Logic

- [x] 3.1 Add "sync" to the MODES array in `ui/app.js`
- [x] 3.2 Add `getModeLabel` mapping for sync → "Sync"
- [x] 3.3 Add `renderSync` function that sets the status text to "Step 1/3. Downloading collection updates..."
- [x] 3.4 Add sync case to the `render()` switch statement, showing `mode-sync` section and `actions-sync` group
- [x] 3.5 Add sync to hash routing in `applyHash()` function

## 4. Verification

- [x] 4.1 Navigate to `#sync` and verify the view renders with correct layout, label, status text, and button
