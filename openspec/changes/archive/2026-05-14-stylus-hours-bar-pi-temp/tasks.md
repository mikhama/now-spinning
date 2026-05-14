## 1. Backend — Stylus Capacity Model

- [x] 1.1 Add `capacity_min` (default 800) and `capacity_max` (default 1000) float fields to Stylus model in `api/models.py`
- [x] 1.2 Update mock stylus data in `api/mock_data.py` with capacity_min/capacity_max values

## 2. Backend — Pi Temperature Endpoint

- [x] 2.1 Add `GET /temperature` endpoint in `api/main.py` that reads `/sys/class/thermal/thermal_zone0/temp` and returns `{"celsius": <float>}`
- [x] 2.2 Add mock/fallback temperature (45.0) when sysfs file is unavailable (boardless mode)

## 3. Frontend — Top Bar Redesign

- [x] 3.1 Replace `#stylus-hours-display` span in `index.html` top bar with compact bar container + temperature span
- [x] 3.2 Add CSS for compact stylus bar (≈4rem × 0.5rem, rounded, paper-dark background, colored fill)
- [x] 3.3 Add CSS for temperature display (DM Mono, ink-mute color)

## 4. Frontend — Stylus Mode Full Bar

- [x] 4.1 Add full-size bar markup to the `#mode-stylus` section in `index.html`
- [x] 4.2 Add CSS for full bar (≈20rem × 1rem, same color logic as compact bar)
- [x] 4.3 Update `renderStylus()` in `app.js` to set full bar width and color based on hours vs capacity

## 5. Frontend — Data & Rendering Logic

- [x] 5.1 Add `temperature` fetch (GET /temperature) on init and every 30s in `app.js`
- [x] 5.2 Update top bar render logic to set compact bar width/color and temperature text
- [x] 5.3 Add bar color helper function: returns `--ink-soft` if hours < capacity_min, `--amber-deep` otherwise
- [x] 5.4 Clamp bar fill ratio to [0, 1] using `Math.min(hours / capacity_max, 1)`
