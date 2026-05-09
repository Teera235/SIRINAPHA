# สถาปัตยกรรมระบบ (Architecture Overview)

สรุปย่อของสถาปัตยกรรม SIRINAPHA Baan-Pla Link — ดูเอกสารฉบับเต็มที่ [`.kiro/specs/sirinapha-baan-pla-link/design.md`](../.kiro/specs/sirinapha-baan-pla-link/design.md)

## High-Level Architecture

```mermaid
%%{init: {'theme':'base','themeVariables':{
  'primaryColor':'#ffffff',
  'primaryTextColor':'#000000',
  'primaryBorderColor':'#000000',
  'lineColor':'#000000',
  'secondaryColor':'#f4f4f4',
  'tertiaryColor':'#eeeeee',
  'fontFamily':'Inter, sans-serif'
}}}%%
flowchart TD
  classDef source fill:#ffffff,stroke:#000000,stroke-width:1px,color:#000000
  classDef pipeline fill:#f4f4f4,stroke:#000000,stroke-width:1.5px,color:#000000
  classDef db fill:#e5e5e5,stroke:#000000,stroke-width:1.5px,color:#000000
  classDef proc fill:#ffffff,stroke:#000000,stroke-width:1px,color:#000000
  classDef app fill:#f4f4f4,stroke:#000000,stroke-width:1.5px,color:#000000
  classDef delivery fill:#ffffff,stroke:#000000,stroke-width:1px,stroke-dasharray:2 2,color:#000000
  classDef user fill:#ffffff,stroke:#000000,stroke-width:1px,color:#000000

  SRC["NOAA OISST / NASA MODIS /<br/>Sentinel-2 / GEBCO / ephem"]:::source
  EB["EventBridge Rules<br/>(daily / every 5 days)"]:::pipeline
  DP["Data Pipeline Lambda<br/>(Python 3.11, retry + validate)"]:::pipeline
  DB[("Supabase PostgreSQL<br/>+ PostGIS + pgcrypto")]:::db

  MM["Mangrove Monitor<br/>(NDVI, Carbon)"]:::proc
  FE["FSI Engine<br/>(6-source score)"]:::proc
  YP["Yield Predictor<br/>(SageMaker ML)"]:::proc

  NA["Next.js App (Vercel)<br/>API Routes + Dashboard"]:::app
  LN["LINE Webhook"]:::delivery
  SM["SMS Fallback"]:::delivery
  WD["Web Dashboard"]:::delivery

  F["ชาวประมงพื้นบ้าน<br/>(LINE หลัก)"]:::user
  C["ตัวแทนชุมชน<br/>(Web + PDF)"]:::user
  P["พันธมิตรองค์กร<br/>(ESG, Blue Carbon)"]:::user

  SRC --> EB
  EB -->|schedule| DP
  DP -->|INSERT raw| DB
  DB -->|READ| MM
  DB -->|READ| FE
  DB -->|READ| YP
  MM -->|INSERT processed| DB
  FE -->|INSERT processed| DB
  YP -->|INSERT processed| DB
  DB --> NA
  NA --> LN
  NA --> SM
  NA --> WD
  LN --> F
  SM --> F
  WD --> C
  WD --> P
```

## Data Flow — Daily FSI Update (06:00 ICT)

```mermaid
%%{init: {'theme':'base','themeVariables':{
  'primaryColor':'#ffffff',
  'primaryTextColor':'#000000',
  'primaryBorderColor':'#000000',
  'lineColor':'#000000',
  'actorBkg':'#ffffff',
  'actorBorder':'#000000',
  'actorTextColor':'#000000',
  'signalColor':'#000000',
  'signalTextColor':'#000000',
  'sequenceNumberColor':'#000000',
  'noteBkgColor':'#f4f4f4',
  'noteBorderColor':'#000000',
  'fontFamily':'Inter, sans-serif'
}}}%%
sequenceDiagram
  participant EB as EventBridge
  participant DP as Data Pipeline
  participant EXT as NOAA / NASA / Sentinel-2
  participant DB as Supabase (PostGIS)
  participant FE as FSI Engine
  participant API as Next.js API
  participant LINE as LINE / SMS
  participant F as ชาวประมง

  EB->>DP: Trigger 06:00 ICT
  DP->>EXT: Fetch SST, Chl-a, NDVI, lunar, season
  note over DP,EXT: retry 3 ครั้ง เว้น 5 นาที
  EXT-->>DP: Raw data
  DP->>DB: Validate schema and INSERT
  EB->>FE: Trigger FSI calculation
  FE->>DB: Read latest raw data
  FE->>FE: Weighted sum และ zone classification
  FE->>DB: INSERT fsi_results และ fsi_component_scores
  API->>DB: Query fishermen + latest FSI
  API->>LINE: Push Thai summary
  LINE-->>F: "สรุป FSI วันนี้ มหาชัย 0.67 เหมาะสม"
  alt LINE ส่งไม่สำเร็จ
    API->>LINE: Fallback to SMS
  end
```

ขั้นตอนหลัก

1. EventBridge เรียก Data Pipeline Lambda
2. Fetchers ดึง SST, Chl-a, NDVI, lunar และ season จากแหล่งภายนอก พร้อม retry 3 ครั้ง เว้น 5 นาที
3. Validator ตรวจ schema แล้ว INSERT เข้า `satellite_raw_data`
4. FSI Engine Lambda อ่านข้อมูลล่าสุดเพื่อคำนวณค่า FSI แบบถ่วงน้ำหนัก
5. INSERT ผลลัพธ์เข้า `fsi_results` และ `fsi_component_scores`
6. API Route `/api/daily-push` ดึงรายชื่อชาวประมงที่ลงทะเบียน สร้างข้อความภาษาไทย แล้วส่งผ่าน LINE
7. กรณี LINE ส่งไม่สำเร็จ ระบบจะ fallback ไปยัง SMS อัตโนมัติ

## เทคโนโลยีหลัก

| Layer | Stack | เหตุผล |
|---|---|---|
| Frontend | Next.js 15 (App Router) + React 19 + TypeScript | unified codebase, Vercel-friendly |
| Maps | Mapbox GL JS + Leaflet (fallback) | GFW-style dark theme |
| Backend | AWS Lambda (Python 3.11) + EventBridge | pay-per-use, scheduled tasks |
| ML | AWS SageMaker | managed inference endpoints |
| Database | Supabase PostgreSQL 15 + PostGIS + pgcrypto | geospatial + column encryption |
| Auth | Supabase Auth | RLS + JWT |
| Messaging | LINE Messaging API, Twilio | Thai market reach |
| Satellite | NOAA ERDDAP, NASA Earthdata, Copernicus | free, well-documented |

## Security

- **RLS policies**: Community_Rep and Corporate_Partner ดูเฉพาะพื้นที่ของตน
- **Column encryption**: `line_user_id`, `phone_number` ผ่าน `pgcrypto`
- **TLS 1.3**: ทุก connection
- **At-rest**: Supabase AES-256

## Data Retention

- Hot storage (PostgreSQL): time-series data 5 ปี
- Cold storage (S3 Glacier): > 5 ปี (processed), > 1 ปี (raw satellite)
- Daily backup: pgdump + S3 upload
