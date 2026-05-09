# เอกสารงานวิจัยและพัฒนา (Research & Development Document)

---

<div align="center">

## SIRINAPHA : Baan-Pla Link
### แพลตฟอร์มแผนที่ข้อมูลประมงแบบมืออาชีพ
### (Professional Fisheries Intelligence Dashboard)

**การออกแบบและพัฒนา Dashboard แบบ Global Fishing Watch สำหรับชุมชนประมงพื้นบ้านไทย**

---

**Design and Development of a Global-Fishing-Watch-Style Dashboard**
**for Small-Scale Fisheries Communities in Thailand**

---

![SIRINAPHA Logo](../../asset/README.md)

---

### ผู้จัดทำ (Author)

**นายธีรทัพ ใยสูงเนิน**
Teerathap Yaisungnoen

---

### ที่ปรึกษาทางเทคนิค (Technical Advisor)
—

### หน่วยงาน (Organization)
SIRINAPHA Research & Development Initiative

---

### ประเภทเอกสาร
เอกสารงานวิจัยและพัฒนา (R&D Document)

### วันที่จัดทำ
10 พฤษภาคม 2569 (10 May 2026)

### เวอร์ชัน
1.0.0 (Initial Draft)

---

</div>

---

## สารบัญ (Table of Contents)

| บท | หัวข้อ | ไฟล์ |
|---|---|---|
| 0 | หน้าปกและสารบัญ | [00-cover.md](./00-cover.md) |
| 1 | บทนำ (Introduction) | [01-introduction.md](./01-introduction.md) |
| 2 | ทฤษฎีและงานวิจัยที่เกี่ยวข้อง (Literature Review) | [02-literature-review.md](./02-literature-review.md) |
| 3 | วิธีการดำเนินงาน (Methodology) | [03-methodology.md](./03-methodology.md) |
| 4 | ข้อกำหนดการออกแบบ (Design Specification) | [04-design-specification.md](./04-design-specification.md) |
| 5 | แผนการพัฒนา (Implementation Plan) | [05-implementation-plan.md](./05-implementation-plan.md) |
| 6 | สรุปและข้อเสนอแนะ (Conclusion) | [06-conclusion.md](./06-conclusion.md) |
| 7 | บรรณานุกรม (References) | [07-references.md](./07-references.md) |
| A | ภาคผนวก A — รายการ API และแหล่งข้อมูล | [appendix-a-data-sources.md](./appendix-a-data-sources.md) |
| B | ภาคผนวก B — ตารางเทียบสี (Color Tokens) | [appendix-b-color-tokens.md](./appendix-b-color-tokens.md) |

---

## บทคัดย่อ (Abstract)

เอกสารนี้นำเสนอการวิจัยและพัฒนา (R&D) สำหรับ Dashboard ของแพลตฟอร์ม **SIRINAPHA : Baan-Pla Link** ซึ่งเป็นระบบสารสนเทศภูมิศาสตร์ (Geospatial Intelligence System) ที่รวมข้อมูลจากดาวเทียม NOAA OISST, NASA MODIS, และ Sentinel-2 เพื่อคำนวณดัชนีความเหมาะสมในการทำประมง (Fishery Suitability Index; FSI) ติดตามสุขภาพป่าชายเลน (Mangrove Health Monitoring) และทำนายผลผลิตสัตว์น้ำ (Yield Prediction) สำหรับชุมชนประมงพื้นบ้านในพื้นที่มหาชัยและระนอง

การออกแบบ User Interface ได้รับแรงบันดาลใจจาก **Global Fishing Watch** [1] ซึ่งเป็นมาตรฐาน de facto ของ geospatial dashboard ระดับสากลในอุตสาหกรรมประมง โดยใช้ธีมสีเข้ม (dark theme) พร้อม cyan accent colors การแสดงข้อมูลราสเตอร์ (raster overlay) แบบเปิด-ปิดได้ และ timeline controls เพื่อการสำรวจข้อมูลเชิงพื้นที่-เวลา (spatiotemporal exploration)

ระเบียบวิธีการคำนวณ FSI ประยุกต์จากแนวคิด **Potential Fishing Zone (PFZ)** ที่พัฒนาโดย Indian National Centre for Ocean Information Services (INCOIS) [2, 3] และแนวคิด **Habitat Suitability Index (HSI)** สำหรับปลาทูน่าและสัตว์น้ำเศรษฐกิจ [4, 5] โดยใช้สูตรถ่วงน้ำหนักระหว่าง SST, Chlorophyll-a, ความลึก, ข้างขึ้นข้างแรม, NDVI และฤดูกาล การจำแนกสุขภาพป่าชายเลนใช้ค่า NDVI threshold อ้างอิงจากงานวิจัยใน Samut Songkhram [6] และ Bhitarkanika [7]

---

**คำสำคัญ (Keywords):** Geospatial Dashboard, Fishery Suitability Index, Potential Fishing Zone, Sea Surface Temperature, Chlorophyll-a, NDVI, Mangrove Health, Blue Carbon MRV, Small-Scale Fisheries, Thailand

---

<div align="center">
<sub>© 2026 SIRINAPHA Project · ใช้งานเพื่อการศึกษาและชุมชนประมงพื้นบ้านไทย</sub>
</div>
