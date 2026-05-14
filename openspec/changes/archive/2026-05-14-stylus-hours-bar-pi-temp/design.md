## Context

The Now Spinning UI runs at 800×480 on a Raspberry Pi touchscreen. The top bar currently displays mode label (left) and stylus hours as plain text (right). The Stylus mode page shows stylus name and hours as text. There's no visual wear indicator or hardware temperature monitoring.

The Stylus model currently has `id`, `name`, and `hours` fields. Stylus cartridges have a manufacturer-specified lifespan range (e.g., 800–1000 hours) that isn't tracked.

## Goals / Non-Goals

**Goals:**
- Show stylus wear visually via a progress bar in the top bar (compact) and Stylus page (full)
- Display Pi CPU temperature in the top bar for hardware health awareness
- Store and use stylus capacity range for color-coded wear indication
- Keep the three-file frontend constraint (no new JS files)

**Non-Goals:**
- Temperature alerts or shutdown automation
- Historical temperature tracking or graphing
- Stylus replacement workflow or notifications
- Changing the Stylus mode navigation (prev/next/reset buttons remain)

## Decisions

### 1. Progress bar rendering — pure CSS with inline width

The bar is a simple `<div>` container with an inner `<div>` whose `width` is set as a percentage via inline style. No canvas, SVG, or external library needed.

- **Ratio calculation**: `hours / capacity_max` clamped to [0, 1]
- **Color logic**: bar fill uses `var(--ink-soft)` when `hours < capacity_min`, switches to `var(--amber-deep)` when `hours >= capacity_min`
- **Alternatives considered**: SVG arc (overcomplicated for a linear bar), CSS gradient (harder to control threshold snap)

### 2. Top bar layout — bar replaces hours text, temperature appended

The right side of the top bar will contain: `[compact bar] [temperature]`

- Compact bar: ~4rem wide, 0.5rem tall, with rounded ends
- Temperature: DM Mono 11px, `var(--ink-mute)`, format "59 °C"
- Hours text removed from top bar (lives only on Stylus page now)

### 3. Stylus page — full bar with hours label

The Stylus mode page shows: stylus name, then a larger bar (~20rem wide, 1rem tall), then hours text below it in DM Mono 1.4rem format "{hours} h". Same color logic as the compact bar.

### 4. Stylus capacity stored in model

Add `capacity_min` and `capacity_max` float fields to the Stylus model (API and mock data). No default values — each stylus must specify its own capacity range since different cartridges have different lifespans.

### 5. Pi temperature — read from sysfs, expose via API

- Backend reads `/sys/class/thermal/thermal_zone0/temp` (millidegrees) and divides by 1000
- Exposed as a field in a new `GET /temperature` endpoint returning `{"celsius": 59.2}`
- On read failure, returns `{"celsius": null}` and logs the error server-side
- UI fetches on init and periodically (every 30s) or receives via WebSocket
- UI shows "N/A" when temperature is null/unavailable

## Risks / Trade-offs

- **[Stale temperature]** → Periodic polling (30s) is sufficient; Pi temp changes slowly
- **[Bar not visible at 0 hours]** → Set minimum visual width of 2px so the bar container is always visible even when empty
- **[Capacity values per-stylus]** → Each stylus stores its own capacity range, since different cartridges have different lifespans
