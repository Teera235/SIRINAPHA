# ภาคผนวก A — รายการ API และแหล่งข้อมูล (Data Sources)

> **กลับไปบทบรรณานุกรม:** [07-references.md](./07-references.md)

---

## A.1 Satellite Data APIs

### A.1.1 NOAA OISST v2 AVHRR

- **Full name:** Optimum Interpolation Sea Surface Temperature, version 2, AVHRR-only
- **Provider:** NOAA National Centers for Environmental Information (NCEI)
- **Resolution:** 0.25° × 0.25° (≈ 28 km)
- **Frequency:** Daily
- **Coverage:** Global, Sep 1981 – present
- **Latency:** 1–2 days (preliminary), 2 weeks (final)
- **Access:**
  - ERDDAP: https://www.ncei.noaa.gov/erddap/griddap/ncdc_oisst_v2_avhrr_by_time_zlev_lat_lon.html
  - NetCDF download: https://www.ncei.noaa.gov/data/sea-surface-temperature-optimum-interpolation/v2.1/access/avhrr/
- **Authentication:** ไม่ต้อง (public)
- **Example query (อ่าวไทย):**

```
https://www.ncei.noaa.gov/erddap/griddap/ncdc_oisst_v2_avhrr_by_time_zlev_lat_lon.json
?sst[(2026-05-09):1:(2026-05-09)]
  [(0.0):1:(0.0)]
  [(5.0):1:(15.0)]
  [(95.0):1:(105.0)]
```

- **Citation:** [8, 9]

### A.1.2 NASA MODIS Aqua Chlorophyll-a

- **Full name:** MODIS-Aqua Level-3 Mapped Monthly/Daily Chlorophyll, OCI algorithm
- **Provider:** NASA Ocean Biology Processing Group (OBPG)
- **Resolution:** 4 km (Level-3 binned), 1 km (Level-2 swath)
- **Frequency:** Daily, Monthly, Annual
- **Coverage:** Global, Jul 2002 – present
- **Access:**
  - Python library: `earthaccess` (https://earthaccess.readthedocs.io/)
  - OPeNDAP: https://oceandata.sci.gsfc.nasa.gov/opendap/MODISA/
  - CMR Search: https://cmr.earthdata.nasa.gov/search/
- **Authentication:** NASA Earthdata Login (ฟรี register)
- **Example Python:**

```python
import earthaccess
earthaccess.login(strategy="netrc")
results = earthaccess.search_data(
    short_name="MODISA_L3m_CHL",
    bounding_box=(95.0, 5.0, 105.0, 15.0),
    temporal=("2026-05-01", "2026-05-09"),
)
files = earthaccess.download(results, local_path="./chla")
```

- **Citation:** [10, 16, 17]

### A.1.3 Sentinel-2 Level-2A (NDVI Source)

- **Full name:** Copernicus Sentinel-2 Level-2A Surface Reflectance
- **Provider:** European Space Agency (ESA) / Copernicus Programme
- **Resolution:** 10 m (B2, B3, B4, B8), 20 m (B5–B7, B8A, B11, B12), 60 m (B1, B9, B10)
- **Frequency:** 5 days at equator (with S2A + S2B)
- **Coverage:** Global land + coastal, Jun 2015 – present
- **Access:**
  - Copernicus Data Space: https://dataspace.copernicus.eu/
  - AWS Open Data: s3://sentinel-s2-l2a/ (requester-pays)
  - Google Earth Engine collection: `COPERNICUS/S2_SR_HARMONIZED`
- **Authentication:** Copernicus Data Space account (ฟรี)
- **Bands for NDVI:** B04 (Red, 665 nm) + B08 (NIR, 842 nm)
- **Citation:** [11]

### A.1.4 GEBCO 2023 Bathymetry

- **Full name:** GEBCO 2023 Global Grid
- **Provider:** General Bathymetric Chart of the Oceans
- **Resolution:** 15 arc-seconds (~450 m at equator)
- **Frequency:** Static (updated annually)
- **Coverage:** Global ocean + land (elevation)
- **Access:**
  - Download: https://www.gebco.net/data_and_products/gridded_bathymetry_data/gebco_2023/
  - Format: NetCDF, GeoTIFF (~7 GB global)
- **Authentication:** ไม่ต้อง
- **Citation:** [12]

### A.1.5 ephem Lunar Phase

- **Full name:** PyEphem astronomical computations
- **Provider:** Python community (author: Brandon Rhodes)
- **Resolution:** On-demand calculation (no data fetch)
- **Access:** `pip install ephem`
- **Example:**

```python
import ephem
moon = ephem.Moon()
moon.compute('2026/05/10')
phase = moon.phase / 100.0  # 0.0 = new moon, 1.0 = full moon
```

- **Citation:** [13]

---

## A.2 Messaging APIs

### A.2.1 LINE Messaging API

- **Provider:** LINE Corporation
- **Docs:** https://developers.line.biz/en/docs/messaging-api/
- **Auth:** Channel access token (long-lived) + channel secret สำหรับ webhook signature
- **Free tier:** 500 broadcast messages/month
- **Paid tier:** ~฿1,500 สำหรับ 15,000 messages/month (Thailand)
- **SDK:** `@line/bot-sdk` (Node.js), `line-bot-sdk-python`

### A.2.2 Twilio SMS (Fallback)

- **Provider:** Twilio Inc.
- **Docs:** https://www.twilio.com/docs/sms
- **Auth:** Account SID + Auth Token
- **Pricing:** ~$0.075 per SMS ไปไทย
- **Alternative:** ThaiBulkSMS (ราคาถูกกว่าแต่ quality ต่ำกว่า)

---

## A.3 Infrastructure & Services

### A.3.1 Supabase

- **Tier:** Free (500 MB database, 2 GB storage, 50k MAU)
- **PostgreSQL:** 15 with PostGIS + pgcrypto extensions
- **Auth:** Email, phone, LINE OAuth
- **API:** Auto-generated REST + GraphQL-like (PostgREST)
- **Docs:** https://supabase.com/docs

### A.3.2 Vercel (Frontend Hosting)

- **Tier:** Hobby (100 GB bandwidth, unlimited static)
- **Features:** Automatic CI/CD จาก GitHub, Edge Functions, ISR
- **Docs:** https://vercel.com/docs

### A.3.3 Mapbox GL JS

- **Free tier:** 50,000 map loads/month
- **Docs:** https://docs.mapbox.com/mapbox-gl-js/
- **Alternative:** MapLibre GL JS (ฟรีไม่จำกัด, ต้องหา tile server เอง)

### A.3.4 AWS Services (Backend)

| Service | Usage | Est. Cost (Phase 1) |
|---|---|---|
| Lambda | Data pipeline, FSI engine | < $5/month (free tier) |
| EventBridge | Scheduling | < $1/month |
| S3 Glacier | Archive > 5 years | < $2/month |
| SageMaker | ML inference | ~$30/month (ml.t2.medium) |
| SNS | Admin alerts | < $1/month |

---

## A.4 Color Reference Standards

### A.4.1 NOAA Ocean Color Standards

- **Reference:** https://oceancolor.gsfc.nasa.gov/
- **Standard ramps:** rainbow, temperature, chlorophyll (logarithmic)

### A.4.2 ColorBrewer 2.0

- **Reference:** https://colorbrewer2.org/
- **Cynthia Brewer (Penn State) — scientifically validated color schemes**

### A.4.3 NASA Earth Observatory Color Tables

- **Reference:** https://earthobservatory.nasa.gov/
- **ใช้สำหรับ:** SST, Chl-a ramps ที่คนทั่วไปคุ้นเคย

---

## A.5 Open Data Portals

| Portal | URL | ข้อมูล |
|---|---|---|
| NASA Earthdata | https://earthdata.nasa.gov/ | MODIS, Landsat, VIIRS |
| NOAA PSL | https://psl.noaa.gov/ | SST, winds, currents |
| Copernicus Marine | https://marine.copernicus.eu/ | EU ocean data |
| Open Data DEM | https://www.opentopography.org/ | Topography |
| Global Fishing Watch | https://globalfishingwatch.org/ | AIS/VMS vessel data [1] |
| Thai GISTDA | https://www.gistda.or.th/ | THEOS, RapidEye (Thailand) |
| NASA Earth Observatory | https://earthobservatory.nasa.gov/ | Articles, sample imagery [15] |

---

## A.6 Thai Government Data Sources

สำหรับ Phase 2 — integrate กับ Thai agencies

| Agency | URL | ข้อมูล |
|---|---|---|
| กรมประมง (DoF) | https://www.fisheries.go.th/ | Catch statistics, licensing |
| กรมทรัพยากรทางทะเลและชายฝั่ง (DMCR) | https://www.dmcr.go.th/ | Mangrove areas, MPAs |
| กรมอุตุนิยมวิทยา (TMD) | https://www.tmd.go.th/ | Weather, seasonal forecast |
| GISTDA | https://www.gistda.or.th/ | Satellite imagery ไทย |
| สำนักงานพัฒนาเทคโนโลยีอวกาศ | https://www.nstda.or.th/ | Space tech data |

---

## A.7 Attribution Requirements

ตาม best practice, เมื่อใช้ข้อมูลเหล่านี้ใน production ต้องแสดง attribution ดังนี้

- **NOAA OISST:** "Sea surface temperature data provided by NOAA OISST v2" [8]
- **NASA MODIS:** "Chlorophyll-a data courtesy of NASA Ocean Biology Processing Group"
- **Sentinel-2:** "Contains modified Copernicus Sentinel data [YEAR]"
- **GEBCO:** "GEBCO 2023 Grid (DOI: 10.5285/f98b053b-0cbc-6c23-e053-6c86abc0af7b)"
- **Mapbox:** "© Mapbox © OpenStreetMap"
- **CartoDB:** "© CARTO © OpenStreetMap"
- **Global Fishing Watch:** "Vessel data from Global Fishing Watch" [1]

สามารถแสดงใน footer ของ dashboard หรือในหน้า "About" ได้

---

> **กลับไปบทบรรณานุกรม:** [07-references.md](./07-references.md)
