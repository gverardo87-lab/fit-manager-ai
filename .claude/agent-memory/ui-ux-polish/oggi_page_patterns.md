---
name: Oggi page design patterns
description: Design system patterns, CSS classes, and component structure for the /oggi cockpit page
type: reference
---

## Oggi Page Architecture

- **Orchestrator**: `frontend/src/app/(dashboard)/oggi/page.tsx` (~226 LOC)
- **CSS**: `oggi-workspace.css` — custom CSS classes at `@layer components` level
- **Hero**: `OggiHero.tsx` — greeting, clock, date, focus brief, stat chips
- **Command Center**: `OggiCommandCenter.tsx` — session dossier with ReadinessRing, alerts, notes, actions
- **Timeline**: `OggiTimeline.tsx` — grouped session list (attention/prepared/internal)
- **Clock**: `AnalogClock.tsx` — SVG analog clock, Apple Watch style

## Custom CSS Class Inventory

- `oggi-hero-mesh` — animated mesh gradient background (20s drift)
- `oggi-command-bar` — hero bar with radial gradients + grain texture
- `oggi-dossier-shell` — command center shell with gradient + grain
- `oggi-rail-shell` — timeline column subtle gradient
- `oggi-notes-shell` — notes section subtle gradient
- `oggi-glow-{teal|amber|red|neutral}` — semantic box-shadow glow (light + dark variants)
- `oggi-lift` — hover translateY(-2px) interaction
- `oggi-session-card` — card transition (transform, border, bg, shadow)
- `oggi-session-card-selected` — selected state translateX(5px)
- `oggi-readiness-halo` — glowing halo behind readiness ring (data-tone attribute)
- `oggi-dossier-glass` — backdrop-filter blur for ring backdrop
- `oggi-dossier-enter` — entrance animation (translateY + scale + opacity)
- `oggi-hero-divider` — teal gradient divider line with reveal animation
- `oggi-title-gradient` — gradient text for "Oggi" title (teal dark-to-light)
- `oggi-scrollbar` — thin 4px scrollbar styling
- `oggi-pulse-dot` — breathing pulse animation (2s cycle)
- `oggi-status-beat` — heartbeat animation for attention dots (2.4s cycle)
- `oggi-clear-dot` — celebratory breathing dot for "all clear" state

## Layout

- 2-column grid: `lg:grid-cols-[minmax(340px,0.84fr)_minmax(0,1.16fr)]`
- Mobile: CommandCenter first (order-1), Timeline after (order-2)
- Desktop: Timeline left (lg:order-1), CommandCenter right (lg:order-2)
- Both columns: `lg:max-h-[calc(100vh-13.5rem)] lg:overflow-y-auto`
- Gap: 4 (gap-4) between all major sections

## Data Flow

- `useWorkspaceToday()` — workspace/today endpoint
- `useSessionPrep()` — workspace/session-prep endpoint
- Sessions sorted by: temporal band (90min/4h/rest) -> attention status -> start time
- PreFlightStatus: ready | incomplete | risk | blocked | no_client

## Surface Role Usage

- Hero: `{ role: "page", tone: "neutral" }` with `oggi-command-bar`
- Command Center: `{ role: "hero", tone: "neutral" }` with `oggi-dossier-shell`
- Timeline: `{ role: "page", tone: "neutral" }` with `oggi-rail-shell`
- Alert blocks: `{ role: "signal", tone: "red"|"amber"|"teal" }`
- Session cards (selected): `{ role: "signal", tone, interactive: true }`
