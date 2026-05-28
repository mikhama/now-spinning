## Why

The frontend currently routes both real UI state changes and unrelated refreshes through the same full `render()` path. Periodic temperature updates, resize recovery, and font-ready rerenders rebuild marquee state even when record metadata did not change, which causes long-text ticker animations to restart and makes the interface feel unstable.

## What Changes

- Update the frontend rendering contract so the app only updates DOM fragments whose underlying state actually changed instead of repainting every visible section through a single shared render pass.
- Preserve marquee continuity for long artist, album, and track fields during unrelated state updates such as temperature polling or stylus-hour events.
- Recompute marquee overflow state only when metadata content changes or when a layout-affecting event requires it.
- Keep the existing view structure, typography, and marquee visual treatment while narrowing when each part of the UI is allowed to rerender.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `ui-app`: Frontend rendering must scope DOM updates to changed UI slices so unrelated refreshes do not reset active metadata marquee animations.

## Impact

- Affected specs: `ui-app`
- Affected frontend code: `ui/app.js`
- Existing marquee markup and styling remain in place; this change focuses on render behavior rather than a new visual treatment
- No backend, API, or data-model changes are expected