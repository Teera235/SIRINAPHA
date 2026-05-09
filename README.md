# SIRINAPHA: Baan-Pla Link

แพลตฟอร์มเชื่อมต่อข้อมูลดาวเทียมกับชุมชนประมงพื้นบ้านในประเทศไทย ใช้ AI วิเคราะห์สุขภาพป่าชายเลน คำนวณดัชนีความเหมาะสมในการทำประมง (FSI) ทำนายผลผลิตสัตว์น้ำ และวางแผนฟื้นฟูอย่างยั่งยืน

## สถาปัตยกรรม (Architecture)

```
ฮักแม่_deck/platfrom/
├── frontend/           Next.js 15 + React 19 + TypeScript + Tailwind
│   ├── src/
│   │   ├── app/        App Router (pages, layouts, API routes)
│   │   ├── lib/        Auth, Supabase, LINE, SMS, delivery service
│   │   └── types/      Shared TypeScript types
│   └── public/
├── backend/            Python 3.11 — AWS Lambda functions
│   ├── lambda/
│   │   ├── shared/         config, models, Supabase client
│   │   ├── data_pipeline/  NOAA, NASA, Sentinel-2, GEBCO, lunar fetchers
│   │   ├── mangrove_monitor/  NDVI, change detection, Blue Carbon MRV
│   │   ├── fsi_engine/     FSI score functions, calculator, map, serializers
│   │   ├── yield_predictor/  ML prediction, revenue forecast, catch ingestion
│   │   ├── restoration_planner/  site analyzer, seedling tracker
│   │   ├── orchestration/  EventBridge config, pipeline orchestrator
│   │   └── data_management/  backup, archival (S3 Glacier)
│   └── conftest.py     pytest config (registers `lambda` as importable package)
├── supabase/
│   └── migrations/     PostgreSQL + PostGIS schema, RLS policies
├── scripts/            Dev scripts (setup, seed, migrate)
├── asset/              Logos, images
├── documents/          Architecture docs, API specs
├── .github/workflows/  CI/CD (backend, frontend)
├── .kiro/specs/        Product specs (requirements, design, tasks)
└── docker-compose.full.yml   Full stack local dev
```

## ภาพรวมของระบบ (System Overview)

ระบบ 4 โมดูลหลัก:

1. **Mangrove Monitor** — ติดตามสุขภาพป่าชายเลนผ่าน NDVI จาก Sentinel-2
2. **FSI Engine** — คำนวณดัชนีความเหมาะสมในการทำประมงจากข้อมูล 6 แหล่ง (SST, Chl-a, Depth, Lunar, NDVI, Season)
3. **Yield Predictor** — ทำนายปริมาณสัตว์น้ำด้วย ML (SageMaker)
4. **Restoration Planner** — วางแผนปลูกป่าชายเลนใหม่ + Blue Carbon MRV

ดูรายละเอียดที่ `.kiro/specs/sirinapha-baan-pla-link/design.md`

## เริ่มต้นใช้งาน (Getting Started)

### Prerequisites
- Node.js 20+
- Python 3.11+
- Docker Desktop (optional — full stack)
- Supabase account (หรือ local Supabase CLI)

### 1. Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local    # เติม SUPABASE + MAPBOX + LINE keys
npm run dev                          # http://localhost:3000
```

### 2. Backend (Python Lambdas)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate               # Windows
pip install -r lambda/requirements.txt
pytest                               # รัน test ทั้งหมด (782 tests)
```

### 3. Database (Supabase)

```bash
# ตัวเลือก A: Supabase Cloud
# รัน SQL จาก supabase/migrations/ ตามลำดับใน SQL editor

# ตัวเลือก B: Supabase CLI local
supabase start
supabase db push
```

## การทดสอบ (Testing)

```bash
# Backend — 782 property-based + unit tests (Hypothesis + pytest)
cd backend && pytest

# Frontend — 80 unit/integration tests (Vitest + Testing Library)
cd frontend && npm test
```

## CI/CD

- **Backend workflow**: `.github/workflows/backend.yml` — lint + pytest บน PR
- **Frontend workflow**: `.github/workflows/frontend.yml` — typecheck + vitest + next build

## เอกสาร (Docs)

- **Requirements**: `.kiro/specs/sirinapha-baan-pla-link/requirements.md`
- **Design**: `.kiro/specs/sirinapha-baan-pla-link/design.md`
- **Tasks**: `.kiro/specs/sirinapha-baan-pla-link/tasks.md`
- **Architecture diagrams**: `documents/`

## Tech Stack

| Layer | Stack |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, Mapbox GL JS, Leaflet |
| Backend | Python 3.11, AWS Lambda, EventBridge, SageMaker, SNS |
| Database | Supabase (PostgreSQL 15 + PostGIS + pgcrypto) |
| Messaging | LINE Messaging API, Twilio (SMS fallback) |
| Satellite | NOAA ERDDAP, NASA Earthdata, Copernicus Data Space, GEBCO, ephem |
| Testing | pytest + Hypothesis (Python), Vitest + fast-check (TS) |

## License

© 2026 SIRINAPHA project. ใช้งานเพื่อการศึกษาและชุมชนประมงพื้นบ้านไทย
