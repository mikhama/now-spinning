## ADDED Requirements

### Requirement: Count only identified local-record playback
A separate history tracker under the playback lock SHALL count positive playback-counter differences independently of stylus availability. Only nonempty IDs resolving to the local `record` table SHALL accrue history. Empty, unresolved, and earlier unknown playback SHALL produce no rows or retroactive attribution.

#### Scenario: Identify a record after unknown playback
- **WHEN** unknown playback is followed by identification of a local record
- **THEN** only counter intervals established after identification SHALL accrue to that record

#### Scenario: No stylus
- **WHEN** a known record plays without any stylus
- **THEN** history SHALL count and save its playback normally

### Requirement: Segment boundaries and timestamps
Each segment SHALL start at its first counted playback interval. Saving part of an open segment SHALL advance its start by the saved duration. Record changes SHALL close the preceding segment before counting a new record. Counter resets SHALL start a new segment. Stop/resume SHALL exclude stopped time.

#### Scenario: Checkpoint followed by stop
- **WHEN** a segment saves 600 seconds and then counts 34 seconds before stop
- **THEN** the next entry SHALL start 600 seconds after the first start and store 34 seconds

#### Scenario: Change and counter reset
- **WHEN** the record changes or its playback counter decreases
- **THEN** the previous positive-duration segment SHALL close before a new counter baseline is established

### Requirement: Ordered retryable checkpoints
History SHALL save at stylus periodic checkpoints, playback stop, stopped stylus changes, Exit, Shut Down, and application cleanup. History SHALL additionally checkpoint after 600 counted unsaved seconds without a stylus. Failed writes SHALL retain all unsaved segments in order, and memory SHALL discard saved seconds only after commit. Retrying or repeated cleanup SHALL NOT duplicate committed seconds.

#### Scenario: Failure spans multiple records
- **WHEN** writes fail while playback changes from A to B and back to A
- **THEN** the tracker SHALL retain all three segments in order and commit them once on successful retry

### Requirement: Independent save attempts and shutdown guard
Both history and stylus saves SHALL be attempted even if either fails. Requested Exit and Shut Down SHALL abort if either save fails. Stylus reset SHALL NOT erase pending history seconds or its playback baseline. Cleanup SHALL retry failed persistence without duplicating previously saved intervals.

#### Scenario: One save fails
- **WHEN** either save fails at an Exit or Shut Down checkpoint
- **THEN** the other save SHALL still be attempted and the power action SHALL be cancelled

#### Scenario: Stylus reset during playback
- **WHEN** a stylus reset clears its pending usage
- **THEN** pending history and subsequent counter differences SHALL remain intact
