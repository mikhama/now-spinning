## ADDED Requirements

### Requirement: Compact stylus bar in top bar
The top bar SHALL display a compact progress bar (approximately 4rem wide, 0.5rem tall) on the right side representing the stylus wear ratio, replacing the previous hours text display.

#### Scenario: Compact bar renders with correct fill
- **WHEN** the active stylus has 600 hours and capacity_max is 1000
- **THEN** the compact bar fill width SHALL be 60% of the bar container

#### Scenario: Bar uses ink-soft color below capacity_min
- **WHEN** the active stylus has 500 hours and capacity_min is 800
- **THEN** the compact bar fill color SHALL be `var(--ink-soft)`

#### Scenario: Bar uses amber-deep color at or above capacity_min
- **WHEN** the active stylus has 850 hours and capacity_min is 800
- **THEN** the compact bar fill color SHALL be `var(--amber-deep)`

#### Scenario: Bar clamped at 100% when hours exceed capacity_max
- **WHEN** the active stylus has 1100 hours and capacity_max is 1000
- **THEN** the compact bar fill width SHALL be 100%

#### Scenario: Compact bar hidden when no styli exist
- **WHEN** no styli are loaded
- **THEN** the compact bar in the top bar SHALL be hidden

### Requirement: Full stylus bar on Stylus mode page
The Stylus mode page SHALL display a larger progress bar (approximately 20rem wide, 1rem tall) with the same color logic as the compact bar, plus hours text displayed below or beside it.

#### Scenario: Full bar renders on Stylus page
- **WHEN** the mode is Stylus and a stylus is selected with 400 hours, capacity_max 1000
- **THEN** the full bar fill width SHALL be 40% and hours text (DM Mono 1.4rem) SHALL show "400 h"

#### Scenario: Full bar color matches threshold logic
- **WHEN** the active stylus has 900 hours and capacity_min is 800
- **THEN** the full bar fill color SHALL be `var(--amber-deep)`

### Requirement: Stylus capacity range storage
Each stylus SHALL have `capacity_min` and `capacity_max` numeric fields representing the manufacturer-specified lifespan range in hours.

#### Scenario: Stylus model includes capacity fields
- **WHEN** a stylus is fetched from the API
- **THEN** the response SHALL include `capacity_min` and `capacity_max` float fields

#### Scenario: Capacity values are required
- **WHEN** a stylus is created or stored
- **THEN** `capacity_min` and `capacity_max` SHALL be explicitly provided (no defaults)

### Requirement: Bar fill ratio calculation
The bar fill ratio SHALL be calculated as `hours / capacity_max`, clamped to the range [0, 1].

#### Scenario: Zero hours
- **WHEN** stylus hours is 0
- **THEN** the bar fill width SHALL be 0% (empty bar, container still visible)

#### Scenario: Hours between 0 and capacity_max
- **WHEN** stylus hours is 750 and capacity_max is 1000
- **THEN** the bar fill width SHALL be 75%
