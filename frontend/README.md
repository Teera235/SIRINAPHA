# SIRINAPHA Frontend

Next.js 15 + React 19 + TypeScript + Tailwind CSS สำหรับ SIRINAPHA Baan-Pla Link Platform

## สั่งเริ่ม

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

เปิด http://localhost:3000

## Scripts

| Script | What |
|---|---|
| `npm run dev` | Dev server (Next.js hot reload) |
| `npm run build` | Production build |
| `npm run start` | Run production build |
| `npm run lint` | ESLint |
| `npm test` | Vitest (run once) |
| `npm run test:watch` | Vitest watch |

## Environment Variables

ดู `.env.local.example` — ต้องการ:

- `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`
- `NEXT_PUBLIC_MAPBOX_TOKEN` (ฟรีที่ mapbox.com)
- `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_CHANNEL_SECRET`
- `TWILIO_*` (หรือ SMS provider อื่น)

## โครงสร้าง

```
src/
├── app/
│   ├── dashboard/
│   │   ├── page.tsx             — Ocean data platform entrypoint (dynamic import)
│   │   ├── layout.tsx
│   │   ├── ocean/               — GFW-style dashboard (modular)
│   │   │   ├── index.ts                  — barrel export
│   │   │   ├── OceanDashboard.tsx        — main composition
│   │   │   ├── LayerControlSidebar.tsx   — left sidebar with layer toggles
│   │   │   ├── TimelineBar.tsx           — bottom time slider
│   │   │   ├── StatusPanels.tsx          — coordinates, lunar, status badge, style switcher
│   │   │   ├── raster-generators.ts      — FSI/SST/Chl-a raster builders (MVP)
│   │   │   ├── map-popups.ts             — Mapbox popup HTML builders
│   │   │   ├── mangrove-alerts.ts        — sample GeoJSON alert data
│   │   │   └── theme.ts                  — design tokens (colors, FSI zones, gradients)
│   │   ├── components/          — legacy components (AlertPanel, NDVIChart, YieldSummary, FSIMap, Sidebar)
│   │   └── carbon/page.tsx      — Blue Carbon MRV report
│   ├── api/
│   │   ├── auth/register/       — POST /api/auth/register
│   │   ├── line/webhook/        — LINE Messaging API webhook
│   │   └── reports/pdf/         — Generate PDF reports
│   ├── layout.tsx
│   ├── page.tsx
│   └── globals.css
├── lib/                         — supabase, auth, line-client, sms-client, delivery-service, etc.
├── types/
│   └── index.ts                 — Shared TS interfaces & constants
└── middleware.ts                — Auth token verification (Supabase)
```

ดู **[documents/research/04-design-specification.md](../documents/research/04-design-specification.md)** สำหรับ design tokens และ component spec แบบละเอียด

## Testing

```bash
npm test                  # run once
npm run test:watch        # watch mode
```

80 tests covering auth validation, LINE webhook, delivery service, SMS client, and message parsing.
