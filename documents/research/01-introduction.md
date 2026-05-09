# บทที่ 1 — บทนำ (Introduction)

> **เอกสารหลัก:** [หน้าปก](./00-cover.md) | **บทถัดไป:** [บทที่ 2 ทฤษฎีและงานวิจัยที่เกี่ยวข้อง](./02-literature-review.md)

---

## 1.1 ที่มาและความสำคัญ (Background and Significance)

### 1.1.1 สถานการณ์ประมงพื้นบ้านไทย

ประเทศไทยมีชาวประมงพื้นบ้าน (small-scale fishermen) จำนวนมากในพื้นที่ชายฝั่งอ่าวไทยตอนใน (Upper Gulf of Thailand) และทะเลอันดามัน ซึ่งพบปัญหาหลัก 3 ประการ ได้แก่

1. **ต้นทุนค่าน้ำมันเชื้อเพลิงสูง** จากการออกเรือหาปลาโดยไม่ทราบตำแหน่งที่เหมาะสมล่วงหน้า ทำให้สิ้นเปลืองเชื้อเพลิงและเวลา
2. **ป่าชายเลนเสื่อมโทรม** จากการบุกรุก การขยายตัวของบ่อกุ้ง และการท่องเที่ยว ส่งผลกระทบต่อแหล่งอนุบาลสัตว์น้ำ (nursery ground) โดยตรง
3. **ขาดเครื่องมือวิเคราะห์เชิงพื้นที่** ในภาษาไทยที่ชาวประมงสามารถใช้ได้จริง ขณะที่เครื่องมือสากล เช่น [Global Fishing Watch (GFW)](https://globalfishingwatch.org/map) [1] ไม่ได้ถูกออกแบบสำหรับประมงพื้นบ้านในบริบทไทย

### 1.1.2 โอกาสจากข้อมูลดาวเทียมฟรี

ในรอบ 10 ปีที่ผ่านมา มีแหล่งข้อมูลดาวเทียมเปิดจำนวนมากที่เข้าถึงได้ฟรี เช่น

- **NOAA OISST v2** — Sea Surface Temperature รายวัน ความละเอียด 0.25° [8, 9]
- **NASA MODIS Aqua Level-3** — Chlorophyll-a concentration รายวัน [10]
- **ESA Sentinel-2** — ภาพถ่ายหลายสเปกตรัม ความละเอียด 10 เมตร รอบโคจรซ้ำ 5 วัน [11]
- **GEBCO 2023 Grid** — ความลึกท้องทะเล 15-arc-second global [12]

ข้อมูลเหล่านี้หากนำมารวมกันและคำนวณเป็นดัชนีเชิงพื้นที่ (spatial index) จะสามารถให้คำแนะนำการทำประมงได้อย่างมีเหตุผลเชิงวิทยาศาสตร์

### 1.1.3 แรงบันดาลใจจาก Global Fishing Watch

[Global Fishing Watch](https://globalfishingwatch.org/map) [1] เป็น platform ที่นำข้อมูล AIS (Automatic Identification System) และ VMS (Vessel Monitoring System) มาแสดงบนแผนที่แบบ interactive โดยใช้ *dark theme + cyan accent + layer toggles + timeline controls* ซึ่งกลายเป็นรูปแบบ (pattern) มาตรฐานของ professional geospatial dashboard ในวงการ ocean & fisheries intelligence

โครงการ SIRINAPHA : Baan-Pla Link ได้รับแรงบันดาลใจจากรูปแบบดังกล่าวและนำมาประยุกต์สำหรับบริบทประมงพื้นบ้านไทย โดย **ยังคงความเป็นมืออาชีพ (professional aesthetic)** แต่เพิ่มความเข้าถึงง่าย (accessibility) ด้วยข้อความภาษาไทยและคำศัพท์ชาวประมงเข้าใจ

---

## 1.2 คำถามวิจัย (Research Questions)

| RQ | คำถาม |
|---|---|
| RQ1 | จะออกแบบ Dashboard ที่รวมข้อมูลดาวเทียมหลายแหล่งและแสดงผลแบบ real-time interactive map ได้อย่างไร ให้มีประสิทธิภาพและสวยงามทัดเทียม Global Fishing Watch |
| RQ2 | สูตรคำนวณ Fishery Suitability Index (FSI) ควรใช้ตัวแปรใดบ้าง และน้ำหนักควรเป็นเท่าใด เพื่อให้เหมาะสมกับประมงพื้นบ้านในอ่าวไทยและอันดามัน |
| RQ3 | เกณฑ์ NDVI classification สำหรับจำแนกสุขภาพป่าชายเลนในบริบทไทยควรเป็นเท่าใด และการตรวจจับการเปลี่ยนแปลง (change detection) ควรใช้วิธีใด |
| RQ4 | จะแสดงข้อมูลเชิงวิทยาศาสตร์ให้ชาวประมงเข้าใจง่ายได้อย่างไร ผ่าน UX/UI ที่เข้าถึงได้ทั้ง desktop และ mobile |

---

## 1.3 วัตถุประสงค์ (Objectives)

### 1.3.1 วัตถุประสงค์หลัก

ออกแบบและพัฒนา Dashboard เชิงสถาปัตยกรรมข้อมูล (Data Dashboard) สำหรับแพลตฟอร์ม SIRINAPHA : Baan-Pla Link ที่มีคุณภาพระดับมืออาชีพ เชื่อมต่อข้อมูลดาวเทียมหลายแหล่ง และใช้งานได้จริงในชุมชนประมงพื้นบ้านไทย

### 1.3.2 วัตถุประสงค์ย่อย

1. **[Obj-1]** ออกแบบ visual theme ในสไตล์ Global Fishing Watch ที่ใช้ dark mode + cyan accent เพื่อสร้างความเป็นมืออาชีพและลด eye strain เมื่อใช้งานต่อเนื่อง
2. **[Obj-2]** กำหนด data layer specification (FSI, SST, Chl-a, NDVI, Lunar, Bathymetry) พร้อม color ramp ที่อ้างอิงมาตรฐานสากล (เช่น NOAA color palettes)
3. **[Obj-3]** สร้าง UI components หลัก ได้แก่ sidebar layer controls, timeline bar, legend panel, info popup, search bar
4. **[Obj-4]** พัฒนาสูตรคำนวณ FSI จากงานวิจัย PFZ และ HSI พร้อมพิสูจน์ความถูกต้องด้วย property-based testing
5. **[Obj-5]** จัดทำเอกสารอ้างอิงตามมาตรฐานวิชาการ พร้อมอ้างอิงจาก peer-reviewed papers

---

## 1.4 ขอบเขตของงาน (Scope)

### 1.4.1 ขอบเขตด้านพื้นที่ (Geographical Scope)

- **พื้นที่นำร่อง Phase 1:** มหาชัย (จ.สมุทรสาคร) และระนอง (จ.ระนอง) ประเทศไทย
- **พื้นที่แสดงผล Dashboard:** แสดงได้ทั่วโลก (global) แต่ focus ที่ชายฝั่งไทย ระหว่าง Lat 5°N–15°N และ Lng 95°E–105°E
- **Bounding Box อ่าวไทยตอนใน (Mahachai):** Lat 13.0°N–13.8°N, Lng 99.8°E–100.8°E
- **Bounding Box ทะเลอันดามัน (Ranong):** Lat 9.5°N–10.5°N, Lng 98.3°E–99.0°E

### 1.4.2 ขอบเขตด้านข้อมูล (Data Scope)

ตามเอกสาร [Requirements](../../.kiro/specs/sirinapha-baan-pla-link/requirements.md) ข้อกำหนดที่ 1

| แหล่งข้อมูล | ความละเอียด | ความถี่ | API |
|---|---|---|---|
| NOAA OISST v2 SST | 0.25° | รายวัน | ERDDAP [9] |
| NASA MODIS Aqua Chl-a | 4 km | รายวัน | earthaccess [10] |
| ESA Sentinel-2 NDVI | 10 m | 5 วัน | Copernicus Data Space [11] |
| GEBCO Bathymetry | 15 arc-sec | static | download [12] |
| ephem Lunar Phase | — | รายวัน (คำนวณ) | Python ephem [13] |

### 1.4.3 ขอบเขตด้านผู้ใช้

- **Primary:** ชาวประมงพื้นบ้าน (Fisherman) — รับข้อมูลผ่าน LINE/SMS และดู web (read-only)
- **Secondary:** ตัวแทนชุมชน (Community Representative) — ใช้ web dashboard เต็มความสามารถ
- **Tertiary:** พันธมิตรองค์กร (Corporate Partner) — เข้าถึงข้อมูล Blue Carbon MRV ตามระดับสมาชิก

### 1.4.4 สิ่งที่ไม่อยู่ในขอบเขต

- ไม่ครอบคลุมการ deploy ไปยัง AWS production (อยู่ในเอกสาร deployment แยก)
- ไม่ครอบคลุม ML model training (อยู่ในเอกสาร yield-predictor แยก)
- ไม่รวม mobile native app (เน้น responsive web เท่านั้นใน Phase 1)

---

## 1.5 ประโยชน์ที่คาดว่าจะได้รับ (Expected Benefits)

### 1.5.1 ด้านเทคนิค

1. Dashboard ที่มีคุณภาพระดับมืออาชีพ (professional-grade) สำหรับ geospatial fisheries intelligence บริบทไทย
2. Reference architecture ที่สามารถต่อยอดได้สำหรับโครงการด้าน ocean data ในอนาคต
3. โค้ดเปิด (open components) ที่ชุมชน GIS/remote sensing ของไทยสามารถนำไปศึกษา

### 1.5.2 ด้านสังคมและเศรษฐกิจ

ตามเป้าหมาย KPI Phase 1 ที่ระบุใน [Requirements](../../.kiro/specs/sirinapha-baan-pla-link/requirements.md)

1. ลดค่าน้ำมันเชื้อเพลิงของชาวประมง **30–40%**
2. เพิ่ม Hit Rate ทำนายพื้นที่ประมง **> 60%**
3. เพิ่มอัตราการรอดตายต้นกล้าป่าชายเลนจาก **45% เป็น 85%**
4. สร้าง Blue Carbon credits ที่มี MRV (Measurement, Reporting, Verification) แม่นยำ

### 1.5.3 ด้านวิชาการ

1. เอกสารงานวิจัยอ้างอิงมาตรฐาน RIFFAI ที่สามารถใช้เป็น reference สำหรับโครงการ geospatial dashboard อื่นในไทย
2. วิธีการคำนวณ FSI ที่พิสูจน์ด้วย property-based tests ครอบคลุม 20 correctness properties

---

## 1.6 โครงสร้างเอกสาร (Document Structure)

เอกสารฉบับนี้แบ่งออกเป็น 7 บทและ 2 ภาคผนวก ตามตารางในหน้าปก

- **บทที่ 2** ทบทวนงานวิจัยที่เกี่ยวข้อง ได้แก่ PFZ, HSI, NDVI thresholds, Blue Carbon, และการออกแบบ dashboard
- **บทที่ 3** อธิบายวิธีดำเนินงาน ทั้ง data pipeline, สูตรคำนวณ, และ UX process
- **บทที่ 4** ข้อกำหนดการออกแบบ (design tokens, components, color palette)
- **บทที่ 5** แผนการ implement แบ่งเป็น milestone
- **บทที่ 6** สรุปผลและข้อเสนอแนะสำหรับ Phase 2 (scaling)
- **บทที่ 7** บรรณานุกรมตาม IEEE citation format

---

## 1.7 นิยามและคำย่อ (Definitions and Abbreviations)

| คำย่อ | ความหมายเต็ม (EN/TH) |
|---|---|
| FSI | Fishery Suitability Index — ดัชนีความเหมาะสมในการทำประมง |
| PFZ | Potential Fishing Zone — พื้นที่ที่มีศักยภาพในการทำประมง |
| HSI | Habitat Suitability Index — ดัชนีความเหมาะสมของถิ่นที่อยู่ |
| SST | Sea Surface Temperature — อุณหภูมิผิวน้ำทะเล |
| Chl-a | Chlorophyll-a — คลอโรฟิลล์-เอ |
| NDVI | Normalized Difference Vegetation Index — ดัชนีพืชพรรณ |
| MRV | Measurement, Reporting, Verification — การตรวจวัด รายงาน และทวนสอบ |
| GFW | Global Fishing Watch |
| OISST | Optimum Interpolation Sea Surface Temperature |
| ERDDAP | Environmental Research Division's Data Access Program |
| CDSE | Copernicus Data Space Ecosystem |
| GEBCO | General Bathymetric Chart of the Oceans |
| AIS | Automatic Identification System |
| VMS | Vessel Monitoring System |

---

> **บทถัดไป:** [บทที่ 2 — ทฤษฎีและงานวิจัยที่เกี่ยวข้อง](./02-literature-review.md)
