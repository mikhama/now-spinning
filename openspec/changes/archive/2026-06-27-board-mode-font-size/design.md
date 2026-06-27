## Context

The frontend is a static three-file UI served by Flask from `ui/`. Its current stylesheet defines physical display sizing variables and a calculated `font-size` directly on `html`, so the root font-size is applied in every runtime mode. That conflicts with the requested behavior: normal board mode must not set a root font-size on the `<html>` element, while boardless mode may continue using the calculated value for local simulation readability.

There is also an existing `ui-design-system` requirement that describes the calculated root font-size as global behavior. The spec phase for this change needs to update that contract so the calculation is scoped to boardless mode only.

## Goals / Non-Goals

**Goals:**
- Ensure normal board mode leaves `<html>` without an explicit font-size declaration.
- Preserve the current calculated root font-size behavior for boardless mode.
- Keep the fixed 800x480 UI layout and existing rem-based sizing model otherwise unchanged.
- Make the boardless styling trigger explicit and testable.

**Non-Goals:**
- Redesign typography, spacing, or the rem scale.
- Change real board event handling, NFC behavior, or WebSocket payload semantics.
- Introduce a frontend framework or external styling dependency.

## Decisions

### Scope root font-size with an explicit boardless root selector

The implementation should move the current `font-size: calc(var(--screen-width) / 50 * var(--dpi-correction))` rule off the unconditional `html` selector and onto a boardless-only root selector, such as `html[data-boardless-mode="true"]`. Normal board mode should render the same `<html>` element without that attribute and without any inline or stylesheet rule that sets `html` font-size.

Alternative considered: set an inline style from JavaScript only in boardless mode. This would satisfy the mode split but makes the styling harder to inspect in CSS and creates a timing dependency during initial render. A root attribute plus CSS keeps the contract declarative.

Alternative considered: keep the unconditional CSS rule and override it in normal mode. Rejected because the requirement is that the font size should not be set at all in usual mode, not merely overridden.

### Let the server expose boardless state at document render time

Because boardless mode is already selected server-side with `BOARDLESS_MODE=true`, the backend should make that state available before the UI stylesheet is applied. The preferred approach is for the `/` route to render or return `index.html` with a boardless marker on `<html>` only when `BOARDLESS_MODE` is true. When the environment variable is unset or false, the served document should have no boardless marker.

Alternative considered: infer boardless mode in the browser from the URL hash or query string. Rejected because boardless mode is an environment/runtime property, not a dev-route choice, and the normal board UI should not depend on client-side guesses.

### Keep physical sizing variables available but inert in normal mode

The `--screen-width`, `--screen-height`, and `--dpi-correction` variables may remain defined on `html` or `:root`; the behavioral change is specifically that the root `font-size` calculation applies only under the boardless root selector. This minimizes layout churn while satisfying the requirement that usual mode does not set the `<html>` font size.

Alternative considered: remove all physical sizing variables outside boardless mode. Rejected because it increases scope and could break CSS that references those variables independently of root font-size.

## Risks / Trade-offs

- [Risk] Existing design-system spec conflicts with the new behavior. -> Mitigation: add a delta spec for `ui-design-system` or update the relevant spec contract so root font-size calculation is boardless-only.
- [Risk] Body dimensions remain in `rem`, so normal mode will use the browser default rem baseline when no root font-size is set. -> Mitigation: verify the normal board viewport still fits 800x480 with no scrolling after implementation.
- [Risk] Server-side document mutation can accidentally add the boardless marker in production. -> Mitigation: centralize the check on `BOARDLESS_MODE` and treat only case-insensitive `"true"` as enabled.
