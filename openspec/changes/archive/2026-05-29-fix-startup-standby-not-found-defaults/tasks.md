## 1. Startup state

- [x] 1.1 Update UI initialization so a cold load without a hash starts in standby with `currentRecordId = null` and `standbyError = "not-found"`.
- [x] 1.2 Remove implicit first-record activation from normal startup data loading while preserving explicit hash-based debug routes.

## 2. Runtime record selection

- [x] 2.1 Verify scan and current-record event handlers are the only paths that activate a record for normal runtime flow.
- [x] 2.2 Reset side and track indexes to the first side and first track whenever a valid record becomes active.

## 3. Rendering defaults

- [x] 3.1 Update standby rendering so pre-scan startup shows the existing record-not-found placeholder instead of record metadata.
- [x] 3.2 Update side-label rendering to use the first available side and fall back to `A` when the first displayed side id is missing.

## 4. Verification

- [x] 4.1 Validate cold-load behavior at the root URL and confirm no record is shown before a scan.
- [x] 4.2 Validate scan outcomes for valid, null, and unknown record ids, including initial Side A display after a successful scan.
- [x] 4.3 Validate that README hash routes such as `#standby`, `#standby-not-found`, and `#play` still render their intended debug views.