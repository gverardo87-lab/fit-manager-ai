# Responsive Density Matrix

Use this matrix to keep visual density coherent while preserving touch usability and page identity.

## Breakpoint targets

| Width | Goal | Layout rule |
|---|---|---|
| `<= 639px` | Touch clarity | Stack sections, compact spacing, avoid more than 2 competing cards above fold |
| `640px - 1023px` | Operational balance | Use 2-column boards, queue/detail pairs, or dossier splits only when they reinforce the desktop archetype |
| `>= 1024px` | Scan speed | Preserve dense desktop hierarchy, asymmetric intent, and avoid mobile-driven oversizing |

## Archetype note

Adapt layout according to the page's real job instead of forcing one shared template:

- `overview dashboard`: summary first, handoff second;
- `operational workspace`: queue or stack must remain dominant over decorative KPI bands;
- `operational workspace`: when many live items are visible, row-dossier lanes should be preferred over repeated tall cards;
- `record page / hub`: identity, status, quick actions, and canonical history must stay legible;
- `ledger / finance dossier`: rows and dossier context can stay denser than a generic CRM card grid.

## Typography and spacing guardrails

| Element | Mobile | Tablet/Desktop |
|---|---|---|
| Primary metric | `text-2xl` minimum | `text-3xl` preferred |
| Secondary metric | `text-base` / `text-lg` | `text-lg` / `text-xl` |
| Labels/meta | `text-[10px]` to `text-xs` | `text-xs` |
| Card padding | `p-3` / `p-4` | `p-4` / `p-5` |
| Dense list row gap | `gap-2` to `gap-2.5` | `gap-3` |
| Workspace header | compact masthead | target `80-96px` height before overflow states |
| Bucket header | 1-2 lines max | single-line lane label when possible |
| Operational queue row | `88-120px` | `72-96px` before expansion |

## Interaction constraints

- Keep primary touch controls at least `h-10`.
- Keep secondary controls at least `h-9`.
- Keep select/button width stable enough to prevent label clipping.
- Keep critical status controls visible without opening extra drawers.
- For queue/detail layouts, keep the selected item or active case obvious across breakpoints.

## Scroll strategy

- For panels with variable-length lists (agenda, alerts, queues), lock panel height and enable internal scroll when it preserves comparison and focus.
- Avoid page-height growth tied to list cardinality.
- Do not force every surface into one long vertical scroll if it weakens comprehension or selection continuity.
- If one utility surface already owns a function such as agenda or quick capture, do not repeat a second card with the same job lower on the page.
