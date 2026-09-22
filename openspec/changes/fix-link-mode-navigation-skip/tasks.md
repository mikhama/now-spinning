## 1. Link Navigation

- [x] 1.1 Update link-mode Prev/Next navigation so dismissing a retained successfully linked record selects the adjacent remaining unlinked record without skipping.
- [x] 1.2 Ensure dismissing the final retained linked record renders the existing no-unlinked-records empty state.

## 2. Regression Coverage

- [x] 2.1 Add dependency-free behavioral tests for normal navigation, adjacent Next/Prev after link success, boundary wrapping, and the final-record empty state.
- [x] 2.2 Run the frontend navigation tests, the existing automated test suite, and OpenSpec validation.
