# SIRINAPHA Backend

Python 3.11 — AWS Lambda functions สำหรับ data pipeline, geospatial analysis, ML inference

## เริ่มต้น

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r lambda/requirements.txt
pytest                          # รัน 782 tests (< 5 วินาที)
```

## โครงสร้าง Lambda

```
lambda/
├── shared/
│   ├── config.py               — env vars, bounding boxes, API endpoints
│   ├── models.py               — dataclasses (FSIInput, NDVIResult, ...)
│   └── supabase_client.py      — factory for supabase-py client
├── data_pipeline/
│   ├── fetchers/
│   │   ├── noaa_sst.py                 — NOAA ERDDAP SST (daily)
│   │   ├── nasa_chl_a.py               — MODIS Aqua Chl-a via earthaccess (daily)
│   │   ├── sentinel2_ndvi.py           — Copernicus Sentinel-2 L2A (5-day cycle)
│   │   ├── gebco_bathymetry.py         — Static GEBCO ocean depth
│   │   └── lunar_phase.py              — ephem library
│   ├── validator.py            — Schema validation before DB insert
│   └── retry.py                — Retry logic (3 attempts, 5-min delay, SNS alert)
├── mangrove_monitor/
│   ├── ndvi_calculator.py      — (NIR - Red) / (NIR + Red), health classification
│   ├── change_detector.py      — 6-month rolling avg, alert thresholds (>20% / >40%)
│   └── carbon_calculator.py    — tCO2/year, revenue sharing (63/20/10/7)
├── fsi_engine/
│   ├── score_functions.py      — sst/chl_a/depth/lunar/season score (all ∈ [0,1])
│   ├── fsi_calculator.py       — weighted sum (0.25 + 0.25 + 0.15 + 0.10 + 0.25 + 0.10)
│   ├── fsi_map.py              — zone classifier + FSI map generator
│   └── serializers.py          — JSON ↔ FSIResult, GeoJSON ↔ FSIResult (round-trip safe)
├── yield_predictor/
│   ├── predictor.py            — SageMaker invoke + response parse
│   ├── revenue_forecast.py     — 7-day / 30-day forecast with confidence intervals
│   └── catch_ingestion.py      — Store real catch reports from LINE
├── restoration_planner/
│   ├── site_analyzer.py        — NDVI history + soil + tide → priority ranking
│   └── seedling_tracker.py     — Track survival rate via NDVI
├── orchestration/
│   ├── eventbridge_config.py   — Schedule rules (daily 06:00 ICT, every 5 days, etc.)
│   └── pipeline_orchestrator.py  — Step-Functions-style DAG runner
├── data_management/
│   ├── backup.py               — Daily snapshot to S3
│   └── archiver.py             — Hot→cold (S3 Glacier) when > 5y (raw) / > 1y (raw)
└── requirements.txt
```

## Testing

ใช้ pytest + Hypothesis สำหรับ property-based tests

```bash
pytest                           # ทั้งหมด
pytest lambda/fsi_engine/        # โมดูลเดียว
pytest -k "property_"            # property tests เท่านั้น
pytest -v --tb=short             # verbose
```

### Notes ในการรัน
- Package ชื่อ `lambda` เป็น Python keyword — `conftest.py` ลงทะเบียน alias `lbd` ให้ใช้ได้
- ทุก import module ใช้ `importlib.import_module("lambda.xxx")` เพื่อหลบ keyword clash

## Property-Based Tests (Hypothesis)

ทดสอบคุณสมบัติที่ต้องเป็นจริงสำหรับทุกอินพุต (ดู `.kiro/specs/sirinapha-baan-pla-link/design.md` Section "Correctness Properties")

- Property 1: FSI weighted sum formula
- Property 2: Score functions range [0,1]
- Property 3: FSI range invariant
- ... (Properties 4-20 ครบในเอกสาร design)

## Deploy

Production deploy บน AWS Lambda (Python 3.11 runtime, ap-southeast-1)
- EventBridge rules: `orchestration/eventbridge_config.py`
- SNS topic: admin alerts (retry failures, data validation errors)
- SageMaker: Yield predictor endpoint
- S3 Glacier: archival storage (>5 years)
