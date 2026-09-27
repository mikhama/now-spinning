## Context

`ui/app.js` stores the selected side and song separately. Its Play navigation handlers currently change both when they reach the first or last song. Boardless elapsed-time updates already resolve songs within the selected side, and manual navigation rebases the playback offset to the selected song's start.

## Goals / Non-Goals

**Goals:**

- Cycle Next and Prev through the songs of the selected side in both directions.
- Keep the selected side and side label stable while navigating songs.
- Keep later elapsed-time updates aligned with the manually selected song.

**Non-Goals:**

- Change the Side button, new-record selection, or side advancement on stop.
- Change record storage or estimated track durations.
- Change the visual design of the Play controls.

## Decisions

### Wrap the track index within the selected side

Each navigation handler will use the current side's track count to wrap its track index. It will leave `currentSideIndex` untouched. If the selected side has no tracks, navigation will do nothing. Using the side's own count also handles sides with different numbers of songs. The alternative of selecting the adjacent side at a track boundary is the behavior being corrected.

### Rebase correction after a manual wrap

After selecting a song, the handler will keep using `getTrackStartSeconds` and `setManualPlaybackOffset` for Play mode. This gives a wrap from the last song to the first song a new effective playback position at the start of the same side. Subsequent status updates continue from that position. The existing Side button and stop handler retain their separate side-change rules.

## Risks / Trade-offs

- [Risk] A side with no songs has no valid destination. → Keep its selection unchanged and do not calculate a playback correction.
- [Risk] Estimated durations can be missing. → Keep using the existing track-start calculation; song selection still follows the track list.

## Migration Plan

No data migration is needed. Deploy the updated browser script; reverting it restores the previous navigation behavior.

## Open Questions

None.
