# Cinematic UI Design Guide - LeadForgeAI

This document defines the interface design tokens, theme palettes, interactive effects, WebGL settings, and animation timelines for LeadForgeAI's premium SaaS dashboard.

---

## 1. Aesthetic Identity & Theme

LeadForgeAI combines **Obsidian Glassmorphism** with **Persian Architectural Geometry** to create a stunning, immersive space-themed command center.

- **Persian Architectural Geometry**: Subtle grid layouts, arch-shaped glowing vector contours, and symmetrical holographic layouts.
- **Glassmorphic Panes**: Floating, translucent panels showing blur values, thin border strokes, and backdrop reflections.
- **Floating Holograms**: Glowing vector elements projecting metric graphs and agent processes with keyframe glow oscillations.

---

## 2. Color Tokens & Typography

### 2.1. Color Palette

| Name | Hex | Purpose |
| :--- | :--- | :--- |
| **Obsidian Background** | `#030303` | Core workspace canvas |
| **Deep Charcoal** | `#0a0a0a` | Container/card backgrounds |
| **Persian Turquoise** | `#00e5ff` | Primary interactive elements, highlights, indicators |
| **Persian Indigo** | `#4f46e5` | Core gradients and ambient background glows |
| **Persian Blue** | `#1e3a8a` | Secondary action highlights |
| **Text Primary** | `#f7f7f7` | Titles and primary descriptions |
| **Text Secondary** | `#a3a3a3` | Body copies, metadata, and labels |

### 2.2. Typography Guidelines
- **Display Typography**: **Outfit** (Sans-serif, geometric-arch style, letter-spacing: `-0.02em` for headlines).
- **Body Copy**: **Inter** (Highly legible sans-serif for reading logs, tables, and forms).
- **Monospace Log Details**: **JetBrains Mono** (Command prompt consoles, data arrays, and status prints).

---

## 3. Glassmorphism Design System

All cards and modals must use the glass styling properties defined in `frontend/tailwind.config.ts`.

### 3.1. Glass Card Styles
```css
.glass-panel {
  background: rgba(10, 10, 10, 0.6);
  backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.05);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5), 
              inset 0 0 1px 0 rgba(255, 255, 255, 0.1);
}
```

### 3.2. Hover States
Interactive components should transition borders to a higher brightness and increase drop shadows:
```css
.glass-panel:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(0, 229, 255, 0.25);
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.7),
              0 0 15px rgba(0, 229, 255, 0.15);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
}
```

---

## 4. Animation & Kinetic Mechanics

- **Lenis Smooth Scroll**: Eliminates browser scroll jitter, creating smooth kinetic inertia.
- **GSAP Timelines**: Custom stagger loops for displaying lead tables and cards sequentially.
- **Framer Motion Transition**:
```typescript
export const fadeInUpTransition = {
  initial: { y: 20, opacity: 0 },
  animate: { y: 0, opacity: 1 },
  transition: { duration: 0.6, ease: [0.16, 1, 0.3, 1] } // Custom cubic ease-out
};
```

---

## 5. 3D WebGL (React Three Fiber & Theatre.js)

### 5.1. Three.js Canvas Setups
- **Renderer**: WebGLRenderer set to `antialias: true`, `alpha: false`, `powerPreference: "high-performance"`.
- **Lighting**:
  - `AmbientLight`: Soft intensity (`0.15`) for base visibility.
  - `DirectionalLight`: Accent source (`0.8` intensity) casting shadows.
  - `PointLight`: Colored glow (turquoise and indigo) matching active coordinates.
- **Post-processing**: Bloom effect (unreal bloom pass) to create glowing holographic vectors.

### 5.2. Theatre.js Timeline & Camera Mechanics
- **Timeline Keyframes**: Dynamic variables mapped to camera coordinates (`x`, `y`, `z`) and look-at positions, synchronizing camera pans as the user navigates between dashboard tabs.
- **Active Dashboard Pan**: Smooth camera zoom-in toward the central holographic grid.
- **Lead Focus Event**: Camera targets the selected lead node on the 3D map, executing a slow orbit.
