# บทที่ 2 — ทฤษฎีและงานวิจัยที่เกี่ยวข้อง (Literature Review)

> **บทก่อนหน้า:** [บทที่ 1 — บทนำ](./01-introduction.md) | **บทถัดไป:** [บทที่ 3 — วิธีการดำเนินงาน](./03-methodology.md)

---

บทนี้ทบทวนวรรณกรรมที่เกี่ยวข้องใน 5 ประเด็นหลัก ได้แก่ (1) Potential Fishing Zone (PFZ) และ Habitat Suitability Index (HSI), (2) Sea Surface Temperature และ Chlorophyll-a ในฐานะตัวแปรการประมง, (3) NDVI และการติดตามป่าชายเลน, (4) Blue Carbon MRV, และ (5) การออกแบบ Geospatial Dashboard สำหรับ Ocean Intelligence

---

## 2.1 Potential Fishing Zone (PFZ) และ Habitat Suitability Index (HSI)

### 2.1.1 แนวคิด Potential Fishing Zone

**Potential Fishing Zone (PFZ)** เป็นกรอบแนวคิดที่ใช้ข้อมูลทางสมุทรศาสตร์หลายตัวแปรจากดาวเทียมเพื่อคาดการณ์พื้นที่ที่มีแนวโน้มพบสัตว์น้ำจำนวนมาก พัฒนาโดย INCOIS (Indian National Centre for Ocean Information Services) และ ISRO ในประเทศอินเดีย ซึ่งมีการใช้งานเชิงปฏิบัติการตั้งแต่ปี ค.ศ. 2000 เป็นต้นมา

Solanki et al. (2010) [2] ได้นำเสนอการใช้ข้อมูลดาวเทียมร่วมกัน (synergistic application) ของ Chlorophyll Concentration (CC), Sea Surface Temperature (SST), และ Sea Surface Wind (SSW) ในการคาดการณ์ PFZ โดยระบุว่า *การใช้ข้อมูลหลายแหล่งร่วมกันช่วยเพิ่มความแม่นยำเมื่อเทียบกับการใช้ตัวแปรเดียว* (ข้อมูลอ้างอิงได้รับการเรียบเรียงใหม่เพื่อปฏิบัติตามข้อกำหนดลิขสิทธิ์)

Mohanty et al. (2023) [3] ขยายกรอบแนวคิดดังกล่าวโดยเพิ่มตัวแปรเชิงพลศาสตร์มหาสมุทร ได้แก่ SST fronts, relative winds, current vectors, Ekman transport และ eddies เพื่อระบุ PFZ ในอ่าวเบงกอล — แนวคิดนี้แสดงให้เห็นว่า *ตัวแปรพื้นฐาน SST และ Chl-a เพียงพอสำหรับการใช้งานเบื้องต้น แต่การเพิ่มตัวแปรพลศาสตร์จะช่วยเพิ่มความละเอียดของ PFZ ในสถานการณ์ฤดูกาลเฉพาะ* (เรียบเรียงใหม่)

### 2.1.2 Habitat Suitability Index (HSI)

**Habitat Suitability Index (HSI)** เป็นดัชนีที่แปลงตัวแปรสิ่งแวดล้อมเป็นค่าระหว่าง 0 ถึง 1 โดยใช้ฟังก์ชัน suitability index (SI) ที่สะท้อนความเหมาะสมของแต่ละตัวแปรต่อสัตว์น้ำเป้าหมาย

Brooks (1997) ตามที่อ้างใน ResearchGate [4] ระบุว่า HSI มีค่าระหว่าง 0 ถึง 1 โดย input คือตัวแปรสิ่งแวดล้อม และ output คือดัชนีความเหมาะสมของถิ่นที่อยู่สำหรับสัตว์น้ำ

Chen et al. (2011) [5] นำเสนอโมเดล HSI สำหรับปลาหมึก Ommastrephes bartramii ในมหาสมุทรแปซิฟิก โดยใช้การถ่วงน้ำหนักระหว่าง SST-based SI และ Sea Surface Height Anomaly (SSHA) ดังสมการ

$$
\text{SI}_{\text{SST-based}} = 0.7 \cdot \text{SI}_{\text{effort-SST}} + 0.3 \cdot \text{SI}_{\text{CPUE-SST}}
$$

แนวคิดการถ่วงน้ำหนักเชิงเส้นนี้ใช้เป็นแม่แบบสำหรับสูตร FSI ของ SIRINAPHA

### 2.1.3 งานวิจัยที่เกี่ยวข้องในอ่าวไทย

Juntarashote et al. (2008) [14] ศึกษาการใช้ภาพเรดาร์ RADARSAT-1 ในการตรวจจับเครื่องมือประมงประจำที่และการเพาะเลี้ยงในอ่าวไทยตอนบน — แสดงให้เห็นว่าพื้นที่มหาชัยและสมุทรสาครมีความเข้มข้นของกิจกรรมประมงสูงและเหมาะกับการทดสอบระบบสารสนเทศทางประมง (เรียบเรียงใหม่)

NASA Earth Observatory [15] รายงานภาพถ่ายกลางคืนจากดาวเทียม Suomi NPP ที่แสดงให้เห็นเรือประมงหมึกจำนวนมากใช้ไฟสีเขียวดึงดูด plankton และปลาในอ่าวไทยและทะเลอันดามัน — ยืนยันว่า *ประมงพื้นบ้านไทยมีการใช้งานพื้นที่ชายฝั่งอย่างหนาแน่น และต้องการเครื่องมือทำนายพื้นที่ที่เหมาะสมเพื่อลดต้นทุนเชื้อเพลิง* (เรียบเรียงใหม่)

---

## 2.2 Sea Surface Temperature และ Chlorophyll-a ในการประมง

### 2.2.1 NOAA OISST v2 — แหล่งข้อมูล SST มาตรฐาน

**NOAA Optimum Interpolation Sea Surface Temperature version 2 (OISST v2)** [8, 9] เป็น dataset มาตรฐานที่ใช้ในงานวิจัยประมงทั่วโลก โดยมีคุณสมบัติหลัก

- **Spatial resolution:** 0.25° × 0.25° (ประมาณ 28 km × 28 km ที่เส้นศูนย์สูตร)
- **Temporal resolution:** รายวัน (daily)
- **Coverage:** ทั่วโลก ตั้งแต่ กันยายน 1981 – ปัจจุบัน
- **Access:** ผ่าน ERDDAP API ฟรี ไม่ต้อง API key

Reynolds et al. (2007) ตามที่อ้างในเอกสาร NCEI [9] อธิบายว่า OISST ใช้เทคนิค Optimum Interpolation (OI) เพื่อรวมข้อมูลจาก AVHRR และ in situ observations ให้เป็น gridded product ที่มีความสม่ำเสมอ

### 2.2.2 NASA MODIS Aqua Chlorophyll-a

**MODIS Aqua Level-3 Mapped Monthly/Daily Chlorophyll-a (OCI algorithm)** [10] เป็น standard product สำหรับ ocean color ในงานประมงและสมุทรศาสตร์

O'Reilly et al. (1998) [16] นำเสนอ OC algorithms สำหรับ SeaWiFS ที่กลายเป็นต้นแบบของ MODIS OC2, OC3M, OC4v4, และ OCI — โดย *Chl-a เป็นตัวแปรทางชีววิทยาเดียวที่สามารถตรวจวัดจากดาวเทียมได้* (เรียบเรียงใหม่) [17] ซึ่งใช้เป็น proxy ของ phytoplankton biomass และเป็นตัวบ่งชี้การมีอยู่ของแพลงก์ตอนซึ่งเป็นอาหารของปลาและสัตว์น้ำ

### 2.2.3 ค่าที่เหมาะสมต่อสัตว์น้ำเศรษฐกิจในอ่าวไทย

Juntarashote et al. [14] และ FAO Aquaculture Technical Papers [18] ระบุช่วงอุณหภูมิที่เหมาะสมสำหรับปลาเศรษฐกิจหลัก

| สัตว์น้ำ | SST ที่เหมาะสม (°C) | Chl-a ที่เหมาะสม (mg/m³) | อ้างอิง |
|---|---|---|---|
| Skipjack tuna (*Katsuwonus pelamis*) | 20–32 (พื้นที่กินอาหาร) | 0.2–2.0 | [18, 19] |
| Yellowfin tuna | 22–30 | 0.1–1.5 | [18] |
| Thai mackerel (*Rastrelliger kanagurta*) | 26–30 | 0.5–5.0 | [3, 14] |
| Indo-Pacific squid | 24–30 | 0.3–3.0 | [15] |
| ปลาทั่วไปในอ่าวไทยตอนใน (สรุป) | **27–30** | **0.5–5.0** | [2, 14] |

Moura et al. (2020) [19] ศึกษา skipjack tuna ใน north Pacific และระบุว่า *การกระจายของปลาสัมพันธ์กับ SST fronts (บริเวณที่มีการเปลี่ยนแปลงอุณหภูมิในแนวนอน) ซึ่งเกิดการสะสมของ plankton และ bait fish* (เรียบเรียงใหม่) — แนวคิด SST fronts นี้สามารถนำไปใช้เป็น feature เพิ่มเติมใน Phase 2

### 2.2.4 สรุปสำหรับสูตร FSI

ด้วยข้อมูลอ้างอิงข้างต้น **SIRINAPHA FSI** กำหนดช่วงคะแนนสูงสุด (score = 1.0) ไว้ที่

- **SST:** 27–30 °C
- **Chl-a:** 0.5–5.0 mg/m³
- **Depth:** 5–50 m (เหมาะสำหรับเรือประมงพื้นบ้านขนาดเล็ก)

ค่านอกช่วงจะลดลงเชิงเส้น (linear decay) ตามรายละเอียดใน [บทที่ 3](./03-methodology.md)

---

## 2.3 NDVI และการติดตามสุขภาพป่าชายเลน

### 2.3.1 NDVI Formula และความหมาย

**Normalized Difference Vegetation Index (NDVI)** คำนวณจากค่าการสะท้อนแสงในแถบ Near-Infrared (NIR) และแถบ Red

$$
\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}
$$

โดยค่าจะอยู่ในช่วง [−1, 1] และ *ค่าที่สูงกว่าบ่งบอกถึงพืชพรรณที่สมบูรณ์กว่า* (เรียบเรียงใหม่) [20]

สำหรับ Sentinel-2 จะใช้ Band 4 (Red, 665 nm) และ Band 8 (NIR, 842 nm) ที่ความละเอียด 10 เมตร

### 2.3.2 เกณฑ์ NDVI สำหรับจำแนกสุขภาพป่าชายเลน

งานวิจัยสำคัญในประเทศไทยและภูมิภาค

**Chaiyarat et al. (2022) [6]** ศึกษาการจำแนกป่าชายเลน 4 ระยะใน Samut Songkhram ด้วย Sentinel-1 C-band backscatter ร่วมกับ Sentinel-2 — ยืนยันว่า *ค่า NDVI เหนือ 0.60 สัมพันธ์กับป่าชายเลนสมบูรณ์ในพื้นที่ศึกษา* (เรียบเรียงใหม่)

**Jongnimit et al. (2024) [21]** วิเคราะห์ Bhitarkanika National Park ด้วย NDVI time-series 30 ปี พบว่าค่า NDVI ของป่าชายเลนสุขภาพดีอยู่ในช่วง 0.55–0.75 ขณะที่พื้นที่เสื่อมโทรมมีค่าต่ำกว่า 0.40

**Songmookda et al. (2017) [22]** (Duke University thesis) เปรียบเทียบป่าชายเลนในไทย (NDVI = 0.61) และมาเลเซีย (NDVI = 0.42) โดยพื้นที่ไทยมีสภาพสมบูรณ์กว่า (เรียบเรียงใหม่)

**Banerjee et al. (2022) [23]** ใน Sundarbans ใช้ NDVI ร่วมกับ NDCI และ NDMI เพื่อแยกระดับสุขภาพป่าชายเลนหลายมิติ แต่ยังยอมรับว่า NDVI เพียงตัวเดียวเป็น *baseline ที่เพียงพอสำหรับระบบ monitoring ที่เน้นความเรียบง่ายและต้นทุนต่ำ* (เรียบเรียงใหม่)

**ZHou et al. (2025) [24]** ใน Quanzhou Bay ใช้ Sentinel-2 ร่วมกับ U-Net และ GAM พบว่า *Kandelia obovata มีโอกาสพบสูงในบริเวณที่ NDVI > 0.43* (เรียบเรียงใหม่) ซึ่งสอดคล้องกับเกณฑ์ "moderate" ของเรา

### 2.3.3 สรุปเกณฑ์ที่ SIRINAPHA ใช้

อ้างอิงจาก [6, 21, 22, 23, 24] และปรับสำหรับบริบทไทย

| สุขภาพ | เกณฑ์ NDVI | คำอธิบาย |
|---|---|---|
| สมบูรณ์ (healthy) | NDVI > 0.60 | ป่าชายเลนธรรมชาติที่ไม่ถูกรบกวน |
| ปานกลาง (moderate) | 0.40 < NDVI ≤ 0.60 | ป่าชายเลนที่ถูกรบกวนเล็กน้อยหรือยังเจริญ |
| เสื่อมโทรม (degraded) | 0.20 < NDVI ≤ 0.40 | พื้นที่ที่มีการเปลี่ยนแปลงหรือถูกบุกรุก |
| วิกฤต (critical) | NDVI ≤ 0.20 | พื้นที่ที่สูญเสียป่าชายเลนหรือตาย |

### 2.3.4 การตรวจจับการเปลี่ยนแปลง (Change Detection)

Luo et al. (2025) [25] (MDPI Water) ใช้ Sentinel-2 time-series ร่วมกับ deep learning ใน Quanzhou Bay เพื่อวินิจฉัยการเสื่อมโทรมของป่าชายเลน โดยใช้ *การลดลงของ NDVI มากกว่า 20% ภายใน 6 เดือน* เป็น threshold สำหรับ "degradation alert" (เรียบเรียงใหม่) ซึ่งสอดคล้องกับ Requirement 2.4 ของ SIRINAPHA ที่กำหนด threshold เดียวกัน

---

## 2.4 Blue Carbon MRV และการคำนวณ CO₂

### 2.4.1 ศักยภาพการกักเก็บคาร์บอนของป่าชายเลน

**Zhang et al. (2025) — Nature Communications [26]** ระบุว่า *ป่าชายเลนเก็บกักคาร์บอนอินทรีย์ (Corg) ต่อหน่วยพื้นที่มากกว่าระบบนิเวศอื่นเกือบทั้งหมด ยกเว้น tundra และ peatlands* (เรียบเรียงใหม่)

**Alongi (2020) — Global Significance of Mangrove Blue Carbon [27]** ระบุค่าเฉลี่ยในการกักเก็บคาร์บอนที่ 179.6 g Corg m⁻² yr⁻¹ หรือประมาณ **6.6 tCO₂/ha/year** (หลังคูณด้วยอัตราแปลง 3.67 = CO₂/C)

**Wang et al. (2021) [28]** ศึกษาจีนและพบว่า *คาร์บอนเหนือดินอยู่ในช่วง 12.0–150.2 Mg/ha ขณะที่คาร์บอนใต้ดินอยู่ในช่วง 46.6–388.6 Mg/ha คิดเป็น 69–91% ของคาร์บอนรวม* (เรียบเรียงใหม่)

### 2.4.2 วิธีคำนวณของ SIRINAPHA

อ้างอิงจาก [26, 27, 28] เราใช้สูตรแบบเรียบง่ายสำหรับ MVP

$$
\text{CO}_2 (\text{tCO}_2/\text{year}) = \text{Area (rai)} \times 0.16 \times f_{\text{NDVI}}(NDVI_{\text{avg}})
$$

โดย
- 1 ไร่ = 0.16 hectare
- $f_{\text{NDVI}}(x) = 6.6 \cdot (x / 0.7)^{1.2}$ — normalize ที่ NDVI = 0.7 ได้ ~6.6 tCO₂/ha/yr ตาม [27]

### 2.4.3 สัดส่วนการแบ่งรายได้

ตาม [Requirements 8.5](../../.kiro/specs/sirinapha-baan-pla-link/requirements.md#ข้อกำหนดที่-8-ระบบ-blue-carbon-mrv-measurement-reporting-verification) กำหนดสัดส่วน

- **ภาคเอกชน:** 63%
- **สหกรณ์ชุมชน:** 20%
- **ภาครัฐ:** 10%
- **ค่าบริการ MRV:** 7%

รวมเป็น 100% โดยมีหลักคิดว่าชุมชนและภาครัฐควรได้รับประโยชน์อย่างน้อย 30% เพื่อให้โครงการยั่งยืน

---

## 2.5 การออกแบบ Geospatial Dashboard สำหรับ Ocean Intelligence

### 2.5.1 Global Fishing Watch (GFW) — Reference Design

**Global Fishing Watch (GFW)** [1] เป็น platform ที่ถือเป็น *de facto standard* ของ geospatial dashboard ในอุตสาหกรรมประมง โดยมีคุณสมบัติสำคัญ

| Feature | รายละเอียด |
|---|---|
| **Theme** | Dark mode พื้นหลังสีน้ำเงินเข้ม (#0a1929 ≈ #0d1b2a) |
| **Accent color** | Cyan (#00e5ff) + teal (#2dd4bf) สำหรับ activity heatmap |
| **Typography** | Inter + monospace สำหรับ coordinates |
| **Layer system** | Sidebar ด้านซ้ายเปิด-ปิด layer ได้ (Apparent fishing effort AIS, VMS, Vessel presence, Detections, Events) |
| **Timeline** | Bottom bar สามารถเลือกช่วงเวลา (YEAR / MONTH / DAY / HOUR) |
| **Vessel info** | คลิก vessel → popup รายละเอียด flag, gear type, IMO |
| **Legend** | Gradient colour ramp พร้อมค่าตัวเลขชัดเจน |

### 2.5.2 งานวิจัยด้าน Geospatial Dashboard UX

Zhang et al. (2021) [29] (MDPI Land) นำเสนอวิธี **Multi-Criteria Decision Analysis (MCDA)** ร่วมกับ weighted linear combinations และ fuzzy analysis สำหรับการประเมินความเหมาะสมของพื้นที่ — แสดงให้เห็นว่า *การรวมตัวแปรหลายตัวด้วยน้ำหนักเชิงเส้นเป็น approach ที่มีประสิทธิภาพและตีความง่าย* (เรียบเรียงใหม่) ซึ่งตรงกับสูตร FSI ที่เราใช้

NOAA CoastWatch (2025) [30] รายงานการนำ satellite-derived Habitat Suitability Index มาใช้เลือกพื้นที่สำหรับ aquaculture siting — แสดงว่า *dashboard ที่ให้ค่า HSI เชิงพื้นที่ช่วยลดเวลาในการ site survey อย่างมีนัยสำคัญ* (เรียบเรียงใหม่)

### 2.5.3 ทางเลือกทางเทคนิคสำหรับ Map Rendering

| เทคโนโลยี | ข้อดี | ข้อเสีย | การใช้งานใน SIRINAPHA |
|---|---|---|---|
| **Mapbox GL JS** | Performance สูง, styling ยืดหยุ่น, data-driven styling | ต้องมี API token, quota limit | ใช้เป็นหลัก (รองรับ raster overlay ที่ดีกว่า) |
| **Leaflet + CartoDB Dark** | Open-source, ไม่ต้อง token, plugin เยอะ | รองรับ vector tiles ได้จำกัด | ใช้เป็น fallback เมื่อไม่มี Mapbox token |
| **deck.gl** | WebGL 3D, 100k+ markers ได้ | Learning curve สูง, bundle ใหญ่ | พิจารณาสำหรับ Phase 2 |
| **MapLibre GL** | Open-source fork ของ Mapbox | ต้องหา tile server เอง | พิจารณาเมื่อย้ายจาก Mapbox |

### 2.5.4 Color Ramp Standards

อ้างอิงจาก NOAA Ocean Color guidelines [31] และ ColorBrewer [32]

**SST Ramp (cold → warm)**
- 15 °C: Deep blue (#1e3cb4)
- 20 °C: Sky blue (#5096dc)
- 25 °C: Light green (#b4dc64)
- 30 °C: Orange (#f0b428)
- 35 °C: Red (#c82820)

**Chlorophyll-a Ramp (low → high)**
- 0.1 mg/m³: Deep purple (#051440)
- 1.0 mg/m³: Dark blue (#0a5078)
- 3.0 mg/m³: Green (#148050)
- 5.0 mg/m³: Yellow-green (#8cbe28)
- 10.0 mg/m³: Yellow (#f0e650)

**FSI Ramp (unsuitable → highly suitable)**
- 0.0: Deep navy (#040f3c)
- 0.3: Teal (#006e8c)
- 0.5: Cyan (#00c8b4)
- 0.7: Green-cyan (#28d4bf)
- 0.9: Lime (#c8d228)
- 1.0: Bright yellow (#ffed4a)

โครงสี FSI ออกแบบให้สอดคล้องกับ **GFW apparent fishing effort heatmap** [1] ที่ใช้ gradient cyan → yellow

---

## 2.6 ช่องว่างงานวิจัย (Research Gap)

จากการทบทวนงานวิจัยข้างต้น พบช่องว่าง 3 ประการที่ SIRINAPHA จะตอบ

1. **ขาด dashboard ประมงพื้นบ้านในบริบทไทย** — GFW [1] และ INCOIS PFZ [2, 3] ถูกออกแบบสำหรับ commercial fleet ระดับสากลและอินเดีย ยังไม่มี platform ที่ออกแบบเฉพาะสำหรับประมงพื้นบ้านไทยที่ใช้ LINE เป็นช่องทางหลัก
2. **การรวม FSI + Mangrove + Blue Carbon ในระบบเดียว** — งานวิจัยส่วนใหญ่แยกระหว่าง fishery forecasting กับ mangrove monitoring ขณะที่ SIRINAPHA รวมทั้งสองเข้ากับ Blue Carbon MRV ในรูปแบบ *single dashboard + single data pipeline*
3. **Property-based testing สำหรับสูตรประมง** — งานวิจัยที่พบยังไม่มี *formal verification* ของสูตร FSI ซึ่ง SIRINAPHA จะเพิ่มด้วย Hypothesis (Python) + fast-check (TypeScript) ครอบคลุม 20 correctness properties ตามเอกสาร [design.md](../../.kiro/specs/sirinapha-baan-pla-link/design.md)

---

## 2.7 สรุปบท

การทบทวนวรรณกรรมในบทนี้ชี้ให้เห็นว่า

1. แนวคิด **PFZ** และ **HSI** เป็นฐานทฤษฎีที่มั่นคงสำหรับการออกแบบ Fishery Suitability Index โดย SST และ Chl-a เป็นตัวแปรหลัก [2, 3, 4, 5]
2. NOAA OISST v2 [8, 9] และ NASA MODIS Aqua [10] เป็น datasets มาตรฐานสากลที่เข้าถึงได้ฟรี เหมาะสำหรับ MVP ของ SIRINAPHA
3. เกณฑ์ NDVI สำหรับสุขภาพป่าชายเลน 0.60 / 0.40 / 0.20 สอดคล้องกับงานวิจัยในไทย [6, 22] และภูมิภาค [7, 21, 23, 24]
4. ค่าคาร์บอนที่กักเก็บ ~6.6 tCO₂/ha/year เป็นค่ากลางที่ยอมรับได้สำหรับ Blue Carbon MRV [26, 27, 28]
5. Global Fishing Watch [1] เป็น reference design ที่เหมาะสมที่สุดสำหรับ professional ocean dashboard ซึ่ง SIRINAPHA จะประยุกต์ใช้โดยคงความเป็น "fisherman-friendly" ผ่านการแสดงผลภาษาไทย

---

> **บทถัดไป:** [บทที่ 3 — วิธีการดำเนินงาน](./03-methodology.md)
