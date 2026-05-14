## MODIFIED Requirements

### Requirement: Persistent top bar
The UI SHALL display a persistent top bar across all modes with `background: var(--paper)`, `border-bottom: 2px solid var(--ink)`, showing the current mode label in DM Mono 11px uppercase on the left. The right side SHALL contain a compact stylus wear bar (≈4rem × 0.5rem) followed by the Pi temperature in DM Mono 11px `color: var(--ink-mute)` format "{int} °C". The previous plain-text stylus hours display is removed from the top bar.

#### Scenario: Top bar displays mode label
- **WHEN** the current mode is "Standby"
- **THEN** the top bar SHALL show "STANDBY" in DM Mono uppercase on the left side with ink-colored text

#### Scenario: Top bar displays compact stylus bar
- **WHEN** a stylus is loaded with 600 hours (capacity_max 1000)
- **THEN** the top bar right side SHALL show a compact progress bar filled to 60%

#### Scenario: Top bar hides compact bar when no styli
- **WHEN** no styli are loaded
- **THEN** the top bar SHALL hide the compact stylus bar entirely

#### Scenario: Top bar displays Pi temperature
- **WHEN** the Pi temperature is 59°C
- **THEN** the top bar right side SHALL show "59 °C" after the stylus bar, in DM Mono ink-mute color

### Requirement: Stylus mode — stylus display with wear bar
In Stylus mode, the UI SHALL display the stylus name, a full-size wear progress bar (≈20rem × 1rem) with capacity-aware coloring, and the hours text below it in DM Mono 1.4rem showing "{hours} h".

#### Scenario: Stylus page shows full bar and hours
- **WHEN** the mode is Stylus and a stylus has 750 hours (capacity_min 800, capacity_max 1000)
- **THEN** the page SHALL show stylus name, a bar filled to 75% in `var(--ink-soft)` color, and text "750 h"

#### Scenario: Stylus page bar color changes at threshold
- **WHEN** the stylus has 850 hours (capacity_min 800)
- **THEN** the full bar fill SHALL use `var(--amber-deep)` color
