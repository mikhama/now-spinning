## Why

The top bar currently shows only raw stylus hours as text, which doesn't convey at-a-glance wear status. Users need a visual indicator of stylus lifespan consumption and Pi temperature for hardware health monitoring — both visible without navigating away from the current mode.

## What Changes

- Replace the stylus hours text in the top bar with a small progress bar showing stylus wear ratio
- Add Pi temperature reading to the top bar (e.g., "59 °C")
- On the Stylus mode page, show a larger progress bar plus the hours text
- Store stylus capacity range (min/max hours) alongside the stylus data — required per-stylus, no defaults
- Bar color logic: `--ink-soft` when hours < capacity min, `--amber-deep` when hours >= capacity min
- Backend exposes Pi CPU temperature via API; returns `null` and logs error when sysfs unavailable

## Capabilities

### New Capabilities
- `stylus-capacity-bar`: Visual progress bar component for stylus wear, with capacity-aware coloring and two sizes (compact for top bar, full for Stylus page)
- `pi-temperature`: Backend endpoint and UI display for Raspberry Pi CPU temperature

### Modified Capabilities
- `ui-app`: Top bar layout changes (bar replaces hours text, temperature added); Stylus mode gains larger bar display

## Impact

- **UI**: `ui/index.html`, `ui/style.css`, `ui/app.js` — top bar and stylus mode section changes
- **API/Models**: `api/models.py` Stylus model gains `capacity_min` and `capacity_max` fields; new `/temperature` endpoint or temperature included in existing data
- **Backend**: New system call to read Pi CPU temperature (`/sys/class/thermal/thermal_zone0/temp`)
- **Mock data**: `api/mock_data.py` updated with capacity values and mock temperature
