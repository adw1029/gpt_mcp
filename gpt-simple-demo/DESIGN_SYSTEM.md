# Design System — Apple-Inspired Light UI

This document describes the visual design language used in this project.
Pass it to an AI to replicate the same style in a new page, component, or project.

---

## 1. Overall Aesthetic

- **Inspiration**: Apple.com / macOS — clean, airy, premium light-mode UI.
- **Mood**: Data-dense but uncluttered. Soft whites and grays with a single confident blue accent.
- **Mode**: Light only. No dark-mode toggle.
- **Framework**: React + custom CSS (no Tailwind). Bootstrap 5 loaded globally but treated as a fallback; all primary styling is handwritten.

---

## 2. Color Palette

### Backgrounds & Surfaces

| Role | Hex |
|------|-----|
| Page background | `#f5f5f7` |
| Alt / off-white page | `#fbfbfd` |
| Card / panel surface | `#ffffff` |
| Subtle gray chrome | `#e8e8ed` |
| Dividers / separators | `rgba(0, 0, 0, 0.06)` |
| Card border | `rgba(0, 0, 0, 0.04)` |

### Text

| Role | Hex |
|------|-----|
| Primary text | `#1d1d1f` |
| Secondary / muted | `#86868b` |
| Disabled / placeholder | `#aeaeb2` |

### Interactive Blue (primary brand color)

| Role | Hex |
|------|-----|
| Default | `#0066cc` (`#06c`) |
| Hover | `#0077ed` |
| Alt (semantic search pages) | `#0071e3` |
| Focus ring | `rgba(0, 102, 204, 0.15)` |

### Status / Semantic Colors

| Role | Hex |
|------|-----|
| Success / approved | `#16a34a` |
| Error / rejected | `#dc2626` |
| Warning / pending | `#f59e0b` |
| In-progress / info | `#2563eb` |

### Domain Accent Colors (used in charts and badges)

| Domain | Hex |
|--------|-----|
| Insurance | `#3b82f6` |
| Title | `#8b5cf6` |
| Chart accent 3 | `#ec4899` |
| Chart accent 4 | `#f59e0b` |
| Chart accent 5 | `#10b981` |

---

## 3. Typography

### Font Stack

```css
font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text',
             'Helvetica Neue', Helvetica, Arial, sans-serif;
```

Monospace (code, IDs, logs):
```css
font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
```

### Scale and Weights

| Use | Size | Weight | Letter-spacing |
|-----|------|--------|----------------|
| Page title / hero | 28–36px | 600 | -1px to -1.5px |
| Section heading | 20–24px | 600 | -0.5px |
| Card title | 16–18px | 600 | -0.3px |
| Body / label | 14–15px | 400–500 | 0 |
| Caption / muted | 12–13px | 400 | 0 |

- **Antialiasing**: always set `-webkit-font-smoothing: antialiased`.
- Heavy/black weights are never used; maximum weight is **600**.

---

## 4. Spacing & Layout

| Token | Value |
|-------|-------|
| Sidebar width | 260px |
| Page horizontal padding | 2rem–2.5rem |
| Card internal padding | 1.5rem–3rem (responsive) |
| Grid gap (dashboards) | 1rem–2rem |
| Content max-width | 1200px–1600px centered |

---

## 5. Border Radius

| Element | Radius |
|---------|--------|
| Cards, panels, modals | **18px** |
| Inner blocks, inputs, tooltips | 12px |
| Small tags, chips, form controls | 10px–12px |
| Buttons (primary & secondary) | **980px** (full pill) |
| Status badges / pills | 980px |
| Avatars, icon containers | 50% or 12px |

---

## 6. Shadows & Elevation

```css
/* Default card resting shadow */
box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);

/* Hover / lifted card */
box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);

/* Floating panels, dropdowns */
box-shadow: 0 8px 40px rgba(0, 0, 0, 0.12);

/* Modals / overlays */
box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
```

Shadows are always very soft and never use harsh colored glows (exception: the floating action button uses a blue glow: `0 8px 25px rgba(0, 102, 204, 0.4)`).

---

## 7. Motion & Transitions

### Default easing
```css
transition: all 0.4s cubic-bezier(0.28, 0.11, 0.32, 1);
```
Use for cards, buttons, panels — the Apple "snap" curve.

### Short interactions (tab switches, toggles)
```css
transition: all 0.2s cubic-bezier(0.28, 0.11, 0.32, 1);
```

### Card / button hover micro-interaction
```css
/* Lift */
transform: translateY(-2px);   /* cards */
transform: translateY(-1px);   /* buttons */

/* Subtle scale */
transform: scale(1.02);        /* icon buttons */
```

### Floating action button pulse
```css
@keyframes pulse {
  0%, 100% { box-shadow: 0 8px 25px rgba(0, 102, 204, 0.4); }
  50%       { box-shadow: 0 8px 35px rgba(0, 102, 204, 0.6); }
}
animation: pulse 2s ease-in-out infinite;
```

---

## 8. Key Components

### Card
```css
.card {
  background: #ffffff;
  border-radius: 18px;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.04);
  transition: all 0.4s cubic-bezier(0.28, 0.11, 0.32, 1);
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}
```

### Primary Button
```css
.btn-primary {
  background: #0066cc;
  color: #ffffff;
  border: none;
  border-radius: 980px;
  padding: 0.625rem 1.5rem;
  font-size: 0.9375rem;
  font-weight: 500;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.28, 0.11, 0.32, 1);
}
.btn-primary:hover {
  background: #0077ed;
  transform: translateY(-1px);
}
```

### Secondary Button
```css
.btn-secondary {
  background: #ffffff;
  color: #1d1d1f;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 980px;
  padding: 0.625rem 1.5rem;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.28, 0.11, 0.32, 1);
}
.btn-secondary:hover {
  background: #f5f5f7;
}
```

### Status Badges
```css
/* General pattern */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.3rem 0.75rem;
  border-radius: 980px;
  font-size: 0.75rem;
  font-weight: 600;
}
/* Variants */
.status-badge.success  { background: rgba(22, 163, 74, 0.1);  color: #16a34a; }
.status-badge.error    { background: rgba(220, 38, 38, 0.1);  color: #dc2626; }
.status-badge.warning  { background: rgba(245, 158, 11, 0.1); color: #d97706; }
.status-badge.info     { background: rgba(37, 99, 235, 0.1);  color: #2563eb; }
```

### Form Input
```css
.form-control {
  border: 1.5px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-family: inherit;
  font-size: 0.9375rem;
  background: #ffffff;
  color: #1d1d1f;
  transition: all 0.3s cubic-bezier(0.28, 0.11, 0.32, 1);
}
.form-control:focus {
  outline: none;
  border-color: #0066cc;
  box-shadow: 0 0 0 4px rgba(0, 102, 204, 0.1);
}
```

### Sidebar (frosted glass, fixed left)
```css
.sidebar {
  width: 260px;
  height: 100vh;
  position: fixed;
  left: 0; top: 0;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(0, 0, 0, 0.06);
}
/* Active nav item */
.nav-item.active {
  background: #f5f5f7;
  color: #0066cc;
  border-radius: 12px;
}
```

### Floating / Glass Panels (chat, modals)
```css
.glass-panel {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border-radius: 16px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}
```

---

## 9. Icons

- **Library**: Font Awesome 6 (`fas fa-*`, `far fa-*`).
- Loaded via CDN: `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css`
- Icon color always matches surrounding text or uses the primary blue `#0066cc` for interactive icons.

---

## 10. Charts (Recharts)

```js
// Tooltip style
contentStyle={{
  background: '#ffffff',
  border: '1px solid rgba(0,0,0,0.06)',
  borderRadius: '8px',
  boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
  fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
  fontSize: '0.8125rem',
}}
// Grid lines
stroke="#f0f0f0"
// Axis ticks
fill="#86868b" fontSize={12}
```

---

## 11. Do's and Don'ts

| Do | Don't |
|----|-------|
| Use `#f5f5f7` for all page backgrounds | Use pure white `#fff` as the page background |
| Use `18px` radius for cards | Use sharp or heavily rounded (>20px) cards |
| Use pill buttons (`border-radius: 980px`) | Use square or slightly-rounded buttons |
| Use `cubic-bezier(0.28, 0.11, 0.32, 1)` for all transitions | Use `linear` or `ease-in-out` on primary elements |
| Keep shadows very soft (max `0.12` alpha) | Use hard/colored shadows except on CTAs |
| Limit font weight to max 600 | Use 700 / 800 / bold weights |
| Single brand color (`#0066cc`) for interactive elements | Mix multiple brand colors for buttons/links |
| Use `backdrop-filter: blur` for floating panels | Use opaque overlays on nav/chat |
