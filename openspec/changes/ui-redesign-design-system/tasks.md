## 1. CSS Foundation — Variables and Font Faces

- [x] 1.1 Add CSS custom properties to `:root` (all design system colors: --paper, --paper-dark, --cream, --ink, --ink-soft, --ink-mute, --amber, --amber-deep, --vinyl, --gold, --red-ink)
- [x] 1.2 Add @font-face declarations for DM Mono (400, 500), Fraunces (normal 400-900, italic 400-700), and Gloock (400) loading from `fonts/` directory
- [x] 1.3 Set body base styles: background var(--paper), color var(--ink), font-family Fraunces, add radial gradient warm spots, add `body::before` grain texture overlay (feTurbulence, opacity 0.2, pointer-events: none)

## 2. Top Bar Restyle

- [x] 2.1 Restyle `#top-bar`: background var(--paper), border-bottom 2px solid var(--ink), remove box-shadow
- [x] 2.2 Restyle `#mode-label`: font-family DM Mono, 11px, uppercase, letter-spacing 0.2em, color var(--ink)
- [x] 2.3 Restyle `#stylus-info`: font-family DM Mono, 11px, color var(--ink-mute)

## 3. Content Area Typography

- [x] 3.1 Restyle `.record-id`: font-family DM Mono, 12px, uppercase, letter-spacing 0.18em, color var(--ink-mute)
- [x] 3.2 Restyle `.record-artist`: font-family Gloock, 28px, color var(--ink)
- [x] 3.3 Restyle `.record-title`: font-family Fraunces italic, 24px, color var(--amber-deep), line-height 1.2
- [x] 3.4 Restyle `.now-playing`: font-family Fraunces, 20px, color var(--amber-deep), border-top 1px solid var(--ink-soft)

## 4. Cover Image and Placeholder Styling

- [x] 4.1 Restyle `.cover-image`: border 1px solid var(--ink), box-shadow layered (0 1px 0, 0 10px 30px, 0 30px 50px in ink rgba)
- [x] 4.2 Restyle `.cover-placeholder`: background var(--paper-dark), border 1px solid var(--ink-soft), remove old gray styling
- [x] 4.3 Restyle `.cover-placeholder-text`: font-family DM Mono, uppercase, letter-spacing 0.15em, color var(--ink-mute)

## 5. Status Tags and Error States

- [x] 5.1 Restyle `.link-status`: font-family DM Mono, uppercase, letter-spacing 0.15em, color var(--amber-deep), border 1px solid var(--amber-deep), background transparent
- [x] 5.2 Restyle `.error-state`: font-family DM Mono, uppercase, letter-spacing 0.15em, color var(--red-ink), border 1px solid var(--red-ink), background transparent
- [x] 5.3 Restyle `.empty-state`: font-family Fraunces italic, color var(--ink-mute)

## 6. Stylus Mode Typography

- [x] 6.1 Restyle `.stylus-name-display`: font-family Gloock, 32px, color var(--ink)
- [x] 6.2 Restyle `.stylus-distance`: font-family DM Mono, 16px, uppercase, letter-spacing 0.15em, color var(--ink-mute)

## 7. Action Bar and Buttons

- [x] 7.1 Restyle `#action-bar`: background var(--ink), border-top 2px solid var(--ink), remove box-shadow
- [x] 7.2 Restyle `.btn`: background var(--ink), color var(--paper), border 1px solid var(--ink-soft), font-family DM Mono, 14px, uppercase, letter-spacing 0.15em
- [x] 7.3 Update `.btn:hover` and `.btn:active` states to use design system colors (hover: background var(--ink-soft); active: background var(--vinyl))

## 8. Verification

- [x] 8.1 Visually verify all 5 modes render correctly with design system styling in browser at 800×480
- [x] 8.2 Verify error states (NFC Reading Error, Record Not Found, Link Error) display correctly
- [x] 8.3 Verify grain texture does not block touch/click interactions on buttons

## 9. Convert All Sizes to Rem

- [x] 9.1 Set `html { font-size: 16px }` as scaling baseline; convert body `width: 800px` → `50rem`, `height: 480px` → `30rem`
- [x] 9.2 Convert top bar sizes to rem: height 48px → 3rem, padding 20px → 1.25rem, font-sizes 11px → 0.6875rem, gap 8px → 0.5rem
- [x] 9.3 Convert content area sizes to rem: gap 12px → 0.75rem, padding 32px → 2rem, split-grid gap 32px → 2rem, height 320px → 20rem
- [x] 9.4 Convert cover sizes to rem: max-height/width 320px → 20rem, placeholder 280px → 17.5rem, placeholder text 14px → 0.875rem, padding 16px → 1rem
- [x] 9.5 Convert record info sizes to rem: record-id 32px → 2rem (padding 10px/16px/6px → 0.625rem/1rem/0.375rem), artist 42px → 2.625rem, title 32px → 2rem, now-playing 20px → 1.25rem (margin/padding 8px → 0.5rem)
- [x] 9.6 Convert status/error/link sizes to rem: font-size 12px → 0.75rem, margin 8px → 0.5rem, padding 4px/12px → 0.25rem/0.75rem
- [x] 9.7 Convert stylus mode sizes to rem: name 32px → 2rem, distance 16px → 1rem
- [x] 9.8 Convert empty-state font-size 18px → 1.125rem
- [x] 9.9 Convert action bar sizes to rem: height 64px → 4rem, button font-size 14px → 0.875rem
- [x] 9.10 Convert box-shadow px values to rem (1px → 0.0625rem, 10px → 0.625rem, 30px → 1.875rem, 50px → 3.125rem)
- [x] 9.11 Convert info-col height 320px → 20rem and record-id top/right 0px stays as 0
