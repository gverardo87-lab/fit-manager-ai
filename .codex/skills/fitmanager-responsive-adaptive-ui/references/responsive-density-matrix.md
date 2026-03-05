# Responsive Density Matrix

Use this matrix to keep visual density coherent while preserving touch usability.

## Breakpoint targets

| Width | Goal | Layout rule |
|---|---|---|
| `<= 639px` | Touch clarity | Stack sections, compact spacing, avoid more than 2 competing cards above fold |
| `640px - 1023px` | Operational balance | Use 2-column boards for paired panels (`md:grid-cols-2`) |
| `>= 1024px` | Scan speed | Preserve dense desktop hierarchy and avoid mobile-driven oversizing |

## Typography and spacing guardrails

| Element | Mobile | Tablet/Desktop |
|---|---|---|
| Primary metric | `text-2xl` minimum | `text-3xl` preferred |
| Secondary metric | `text-base` / `text-lg` | `text-lg` / `text-xl` |
| Labels/meta | `text-[10px]` to `text-xs` | `text-xs` |
| Card padding | `p-3` / `p-4` | `p-4` / `p-5` |
| Dense list row gap | `gap-2` to `gap-2.5` | `gap-3` |

## Interaction constraints

- Keep primary touch controls at least `h-10`.
- Keep secondary controls at least `h-9`.
- Keep select/button width stable enough to prevent label clipping.
- Keep critical status controls visible without opening extra drawers.

## Scroll strategy

- For panels with variable-length lists (agenda, alerts, queues), lock panel height and enable internal scroll.
- Avoid page-height growth tied to list cardinality.
