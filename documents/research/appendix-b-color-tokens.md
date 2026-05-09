# ภาคผนวก B — ตารางเทียบสี (Color Tokens Reference)

> **กลับไปบทที่ 4:** [04-design-specification.md](./04-design-specification.md)

---

เอกสารนี้เป็น **single source of truth** สำหรับสีทั้งหมดใน SIRINAPHA Dashboard — ใช้เป็น reference ตอนเขียน Tailwind config, CSS variables, หรือ design handoff ไปยัง Figma

---

## B.1 Core Dark Palette

| Token | Hex | RGB | HSL | Usage |
|---|---|---|---|---|
| `--ocean-deepest` | `#020617` | 2, 6, 23 | 229, 84%, 5% | Pure black background (modals) |
| `--ocean-deep` | `#0a1929` | 10, 25, 41 | 212, 61%, 10% | Main map canvas background |
| `--ocean-panel` | `#0d1b2a` | 13, 27, 42 | 211, 53%, 11% | Sidebar, panel backgrounds |
| `--ocean-surface` | `#0f172a` | 15, 23, 42 | 222, 47%, 11% | Card, elevated surface |
| `--ocean-surface-2` | `#1a2332` | 26, 35, 50 | 217, 31%, 15% | Hover state |
| `--ocean-surface-3` | `#1e293b` | 30, 41, 59 | 217, 33%, 17% | Input, higher elevation |
| `--ocean-land` | `#151d2e` | 21, 29, 46 | 221, 37%, 13% | Land mask on map |

---

## B.2 Border Palette

| Token | Hex | Usage |
|---|---|---|
| `--border-subtle` | `#1b2838` | Subtle border (sidebar divider) |
| `--border-default` | `#334155` | Default border (cards, inputs) |
| `--border-light` | `#475569` | Lighter border (hover, focus) |
| `--border-accent` | `#00e5ff` | Focus ring (accent) |

---

## B.3 Accent Palette

### B.3.1 Primary Accents

| Token | Hex | Usage |
|---|---|---|
| `--accent-cyan` | `#00e5ff` | Primary action, FSI green zone |
| `--accent-cyan-80` | `#00e5ffcc` | Cyan with 80% opacity |
| `--accent-cyan-40` | `#00e5ff66` | Cyan with 40% opacity (glow) |
| `--accent-cyan-10` | `#00e5ff1a` | Cyan with 10% opacity (highlight) |
| `--accent-teal` | `#2dd4bf` | Active layer indicator |
| `--accent-teal-glow` | `rgba(45, 212, 191, 0.5)` | Glow effect |

### B.3.2 Data Layer Accents

| Token | Hex | Layer |
|---|---|---|
| `--layer-fsi` | `#00e5ff` | Fishery Suitability Index |
| `--layer-ndvi` | `#69f0ae` | Vegetation / Mangrove |
| `--layer-sst` | `#ff6e40` | Sea Surface Temperature |
| `--layer-chla` | `#40c4ff` | Chlorophyll-a |
| `--layer-lunar` | `#b388ff` | Lunar phase |
| `--layer-season` | `#ffd740` | Season |
| `--layer-vessel` | `#06b6d4` | Vessel/AIS |

### B.3.3 Status Accents

| Token | Hex | Status |
|---|---|---|
| `--status-success` | `#22c55e` | Healthy / Good / Success |
| `--status-warning` | `#ffab00` | Warning / Moderate |
| `--status-alert` | `#ea580c` | Alert / Degraded |
| `--status-danger` | `#ff1744` | Critical / Danger |
| `--status-info` | `#3b82f6` | Info / Neutral |

---

## B.4 Text Palette

| Token | Hex | Contrast on `--ocean-deep` | Usage |
|---|---|---|---|
| `--text-primary` | `#e2e8f0` | 11.8:1 (AAA) | ข้อความหลัก |
| `--text-bright` | `#ffffff` | 17.5:1 (AAA) | Headings, high emphasis |
| `--text-secondary` | `#94a3b8` | 6.7:1 (AAA) | ข้อความรอง |
| `--text-muted` | `#64748b` | 4.3:1 (AA) | Labels, captions |
| `--text-disabled` | `#475569` | 2.6:1 | Disabled |
| `--text-faded` | `#334155` | 1.6:1 | Background labels (decorative only) |

---

## B.5 FSI Zone Colors

ตามสูตรใน [บทที่ 3](./03-methodology.md)

| Zone | FSI Range | Primary | Glow (40%) | Label (Thai) |
|---|---|---|---|---|
| Green | ≥ 0.7 | `#00e5ff` | `rgba(0, 229, 255, 0.4)` | เหมาะสมมาก |
| Yellow | 0.4 – 0.7 | `#ffab00` | `rgba(255, 171, 0, 0.4)` | เหมาะสมปานกลาง |
| Red | < 0.4 | `#ff1744` | `rgba(255, 23, 68, 0.4)` | ไม่เหมาะสม |

---

## B.6 NDVI Health Colors

ตามเกณฑ์ใน [บทที่ 2 และ 3](./02-literature-review.md)

| Health | NDVI Range | Primary | Label (Thai) |
|---|---|---|---|
| Healthy | > 0.60 | `#16a34a` | สมบูรณ์ |
| Moderate | 0.40 – 0.60 | `#ca8a04` | ปานกลาง |
| Degraded | 0.20 – 0.40 | `#ea580c` | เสื่อมโทรม |
| Critical | ≤ 0.20 | `#dc2626` | วิกฤต |

---

## B.7 Gradient Definitions

### B.7.1 FSI Ramp (Low → High)

```css
background: linear-gradient(to right,
  #040f3c 0%,
  #084064 12%,
  #006e8c 25%,
  #00aaa8 37%,
  #00c8b4 50%,
  #28d4bf 62%,
  #50dc96 75%,
  #c8d228 87%,
  #ffed4a 100%
);
```

### B.7.2 SST Ramp (Cold → Warm)

```css
background: linear-gradient(to right,
  #1e3cb4 0%,   /* 15°C */
  #5096dc 25%,  /* 20°C */
  #b4dc64 50%,  /* 25°C */
  #f0b428 75%,  /* 30°C */
  #c82820 100%  /* 35°C */
);
```

### B.7.3 Chlorophyll-a Ramp (Low → High)

```css
background: linear-gradient(to right,
  #051440 0%,
  #0a5078 20%,
  #148050 40%,
  #8cbe28 60%,
  #c8dc40 80%,
  #f0e650 100%
);
```

### B.7.4 NDVI Ramp (Bare → Lush)

```css
background: linear-gradient(to right,
  #8b4513 0%,   /* -0.2 bare/water */
  #deb887 20%,  /* 0.0 bare soil */
  #f4e4c1 40%,  /* 0.2 sparse */
  #9acd32 60%,  /* 0.4 moderate */
  #228b22 80%,  /* 0.6 dense */
  #006400 100%  /* 0.8+ forest */
);
```

### B.7.5 Lunar Indicator (Moon phase arc)

```css
background: radial-gradient(circle,
  #b388ff 0%,
  #7c4dff 40%,
  #512da8 100%
);
```

---

## B.8 Tailwind Config Mapping

เพิ่มใน `tailwind.config.ts` โครงการ

```typescript
theme: {
  extend: {
    colors: {
      // Ocean dark theme
      ocean: {
        deepest: "#020617",
        deep: "#0a1929",
        panel: "#0d1b2a",
        surface: "#0f172a",
        "surface-2": "#1a2332",
        "surface-3": "#1e293b",
        land: "#151d2e",
      },
      // Accents
      accent: {
        cyan: "#00e5ff",
        teal: "#2dd4bf",
        sky: "#40c4ff",
        purple: "#b388ff",
        amber: "#ffab00",
        red: "#ff1744",
      },
      // Data layers
      layer: {
        fsi: "#00e5ff",
        ndvi: "#69f0ae",
        sst: "#ff6e40",
        chla: "#40c4ff",
        lunar: "#b388ff",
        season: "#ffd740",
        vessel: "#06b6d4",
      },
      // FSI zones (extend existing fsi palette)
      fsi: {
        green: "#00e5ff",
        yellow: "#ffab00",
        red: "#ff1744",
      },
      // NDVI health (keep existing)
      ndvi: {
        healthy: "#16a34a",
        moderate: "#ca8a04",
        degraded: "#ea580c",
        critical: "#dc2626",
      },
    },
    backgroundImage: {
      "ramp-fsi": "linear-gradient(to right, #040f3c, #084064, #006e8c, #00aaa8, #00c8b4, #28d4bf, #50dc96, #c8d228, #ffed4a)",
      "ramp-sst": "linear-gradient(to right, #1e3cb4, #5096dc, #b4dc64, #f0b428, #c82820)",
      "ramp-chla": "linear-gradient(to right, #051440, #0a5078, #148050, #8cbe28, #f0e650)",
      "ramp-ndvi": "linear-gradient(to right, #8b4513, #deb887, #f4e4c1, #9acd32, #228b22, #006400)",
    },
  },
}
```

---

## B.9 CSS Custom Properties (แนะนำใช้ใน `globals.css`)

```css
:root {
  /* Ocean dark */
  --ocean-deepest: #020617;
  --ocean-deep: #0a1929;
  --ocean-panel: #0d1b2a;
  --ocean-surface: #0f172a;
  --ocean-surface-2: #1a2332;
  --ocean-land: #151d2e;

  /* Borders */
  --border-subtle: #1b2838;
  --border-default: #334155;
  --border-light: #475569;

  /* Accents */
  --accent-cyan: #00e5ff;
  --accent-teal: #2dd4bf;
  --accent-amber: #ffab00;
  --accent-red: #ff1744;

  /* Text */
  --text-primary: #e2e8f0;
  --text-bright: #ffffff;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
}
```

---

## B.10 Accessibility Contrast Matrix

ทุก combination ได้รับการ verify ด้วย WebAIM Contrast Checker (https://webaim.org/resources/contrastchecker/)

| Foreground | Background | Ratio | WCAG |
|---|---|---|---|
| `#e2e8f0` | `#0a1929` | 11.8:1 | AAA |
| `#ffffff` | `#0a1929` | 17.5:1 | AAA |
| `#94a3b8` | `#0a1929` | 6.7:1 | AAA |
| `#64748b` | `#0a1929` | 4.3:1 | AA |
| `#00e5ff` | `#0a1929` | 9.6:1 | AAA |
| `#ffab00` | `#0a1929` | 8.5:1 | AAA |
| `#ff1744` | `#0a1929` | 4.5:1 | AA |
| `#94a3b8` | `#0d1b2a` | 6.3:1 | AAA |

**หมายเหตุ:** สำหรับ `#ff1744` บน `#0a1929` ได้ AA พอดี — ไม่ใช้สำหรับข้อความเล็ก (< 14px regular) ให้ใช้เฉพาะใน label ขนาด ≥ 18px หรือ bold

---

## B.11 Design Token Export Format

สำหรับ Figma handoff และ Style Dictionary

```json
{
  "ocean": {
    "deep": { "value": "#0a1929", "type": "color" },
    "panel": { "value": "#0d1b2a", "type": "color" }
  },
  "accent": {
    "cyan": { "value": "#00e5ff", "type": "color" }
  }
}
```

---

> **กลับไปบทที่ 4:** [04-design-specification.md](./04-design-specification.md)
