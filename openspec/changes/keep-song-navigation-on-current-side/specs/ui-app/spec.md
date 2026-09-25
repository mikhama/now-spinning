## ADDED Requirements

### Requirement: Play song navigation stays on the selected side
In Play mode, the Prev and Next song controls SHALL cycle through only the songs on the currently selected side. They SHALL leave the selected side and its label unchanged. If that side has no songs, either control SHALL leave the selection unchanged.

#### Scenario: Next wraps from the final song
- **WHEN** the final song on side "A" is selected and the user clicks Next
- **THEN** the first song on side "A" SHALL be selected
- **AND** the selected side and Side button label SHALL remain side "A"

#### Scenario: Prev wraps from the first song
- **WHEN** the first song on side "B" is selected and the user clicks Prev
- **THEN** the final song on side "B" SHALL be selected
- **AND** the selected side and Side button label SHALL remain side "B"

#### Scenario: Navigation on a side with no songs
- **WHEN** the selected side has no songs and the user clicks Prev or Next
- **THEN** the selected side and song index SHALL remain unchanged
