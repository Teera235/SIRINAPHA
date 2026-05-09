# บทที่ 6 — สรุปและข้อเสนอแนะ (Conclusion)

> **บทก่อนหน้า:** [บทที่ 5 — แผนการพัฒนา](./05-implementation-plan.md) | **บทถัดไป:** [บทที่ 7 — บรรณานุกรม](./07-references.md)

---

## 6.1 สรุปงาน

เอกสารฉบับนี้ได้นำเสนอการวิจัยและพัฒนา (R&D) สำหรับ Dashboard ของแพลตฟอร์ม **SIRINAPHA : Baan-Pla Link** โดยมีเป้าหมายหลักคือการออกแบบระบบ geospatial intelligence สำหรับชุมชนประมงพื้นบ้านไทย ที่มีคุณภาพระดับมืออาชีพทัดเทียม **Global Fishing Watch** [1]

ผลลัพธ์สำคัญที่ได้จากงาน

1. **Dashboard design system ครบวงจร** ประกอบด้วย
   - Color tokens 25+ tokens (dark theme + cyan accent)
   - Typography scale 10 ระดับ (Inter + Roboto Mono)
   - Component specifications 7 components หลัก
   - Responsive breakpoints 5 ระดับ + mobile-first graceful degradation
   - Motion guidelines และ accessibility (WCAG AA)

2. **สูตร FSI ที่อ้างอิงจากงานวิจัย** สามารถคำนวณดัชนีความเหมาะสมในการทำประมงจาก SST, Chl-a, Depth, Lunar, NDVI และ Season โดยถ่วงน้ำหนักตามแนวคิด PFZ [2, 3] และ HSI [4, 5] — พร้อมพิสูจน์ความถูกต้องด้วย **20 correctness properties**

3. **เกณฑ์ NDVI สำหรับป่าชายเลนไทย** ที่อ้างอิงจากงานวิจัยใน Samut Songkhram [6] และ Bhitarkanika [21] โดยใช้ threshold 0.60 / 0.40 / 0.20 สำหรับ 4 ระดับสุขภาพ

4. **แนวทางคำนวณ Blue Carbon MRV** ใช้ค่า 6.6 tCO₂/ha/yr เป็น baseline จาก Alongi (2020) [27] พร้อมสัดส่วนแบ่งรายได้ 63/20/10/7 ที่สะท้อน incentive design สำหรับชุมชน

5. **แผนการ implement 4 milestones** ครอบคลุมตั้งแต่ MVP demo จนถึง production pilot 50 ชาวประมง

---

## 6.2 สิ่งที่บรรลุ (Achievements)

เทียบกับวัตถุประสงค์ที่ตั้งไว้ใน [บทที่ 1](./01-introduction.md)

| Obj | รายละเอียด | สถานะ |
|---|---|---|
| Obj-1 | Visual theme สไตล์ GFW (dark + cyan) | เสร็จในบทที่ 4 |
| Obj-2 | Data layer spec + color ramps | เสร็จในบทที่ 4 + ภาคผนวก B |
| Obj-3 | UI components หลัก (sidebar, timeline, popup และอื่น ๆ) | Spec เสร็จ; implementation ปัจจุบัน 80% |
| Obj-4 | สูตร FSI + property-based tests | ผ่าน 782 tests |
| Obj-5 | เอกสารมาตรฐาน RIFFAI + อ้างอิง | เอกสารฉบับนี้ |

---

## 6.3 ข้อจำกัดของงาน (Limitations)

### 6.3.1 ด้านข้อมูล

1. **Raster resolution ต่ำ** (0.5°/720×360) ในปัจจุบัน เพื่อให้ render ได้ใน browser — ไม่เหมาะสำหรับการตัดสินใจในระดับ micro (sub-kilometer)
2. **Simulated data** ยังใช้ Perlin noise function ใน MVP — ข้อมูลจริงต้องผ่าน data pipeline ของ backend
3. **ไม่มีข้อมูล sea current** ซึ่งในงานวิจัย PFZ [3] ระบุว่าเป็น feature สำคัญสำหรับการคาดการณ์

### 6.3.2 ด้าน UX

1. **ยังไม่ได้ usability test** กับชาวประมงจริง
2. **ภาษาไทย-อังกฤษผสม** ในบาง label ต้อง localize ให้สมบูรณ์
3. **ยังไม่มี offline mode** สำหรับชาวประมงที่ออกเรือในพื้นที่ไม่มีสัญญาณ

### 6.3.3 ด้านเทคนิค

1. **ขึ้นกับ Mapbox** ซึ่งมี quota limit (50,000 map loads/month ใน free tier)
2. **Browser compatibility** — รองรับแค่ Chrome/Safari/Firefox รุ่นใหม่ (WebGL 2.0)
3. **WCAG compliance** เต็มรูปแบบยังไม่ได้ตรวจสอบด้วย screen reader ของจริง (ต้องใช้ manual audit)

---

## 6.4 ข้อเสนอแนะสำหรับการทำต่อ (Future Work)

### 6.4.1 Phase 2 (6–12 เดือนข้างหน้า)

1. **Integrate AIS/VMS data** ผ่าน GFW API [1] เพื่อแสดง vessel traffic จริง ลดการชนประมงซ้ำกัน
2. **ML-based FSI refinement** เพิ่ม feature sea current, SST gradient (fronts), และ catch report feedback loop ตาม [30]
3. **Multi-species prediction** แยกทำนายปลาทู, ปลาหมึก, ปู, กุ้ง ตาม niche ของแต่ละ species
4. **Offline PWA mode** ด้วย service worker + cached tiles
5. **IBM Plex Sans Thai** แทน Inter เพื่อการอ่านภาษาไทยที่ดีขึ้น

### 6.4.2 Phase 3 (12–24 เดือน)

1. **Regional expansion** — ขยายไปภาคตะวันออก (ระยอง, ตราด) และภาคใต้ (นครศรีธรรมราช, ปัตตานี)
2. **Carbon credit marketplace integration** — เชื่อม Verra, Gold Standard, ACR
3. **Mobile native app** — React Native สำหรับ push notifications ที่ reliable กว่า
4. **Open data API** — ให้นักวิจัยและองค์กรอื่นเข้าถึง data ได้ (with rate limiting)
5. **Community-generated content** — ชาวประมงรายงานปัญหา mangrove ผ่าน LINE + AI image moderation

### 6.4.3 Research Extensions

1. **Deep learning for species detection** จากภาพถ่ายเรือ (ใช้ YOLO v8 หรือ SAM)
2. **Climate change impact modeling** — ใช้ CMIP6 scenarios ทำนาย FSI ในอนาคต 10–50 ปี
3. **Socioeconomic impact study** — วัดผลกระทบต่อรายได้ชาวประมงอย่างเข้มงวด (RCT)

---

## 6.5 บทเรียนที่ได้ (Lessons Learned)

### 6.5.1 ทางเทคนิค

1. **Raster tile generation ใน client-side** เป็นวิธีเร่งงานช่วงต้น แต่ไม่ scalable — Phase 2 ควรใช้ tile server (TiTiler หรือ rio-tiler)
2. **PostGIS + Supabase** เร็วและง่ายกว่าที่คิด สำหรับ geospatial queries ระดับหลายพัน records
3. **Property-based testing** ด้วย Hypothesis/fast-check จับบัคที่ unit test ดั้งเดิมไม่เจอได้หลาย edge case

### 6.5.2 ทาง UX

1. **Dark theme มีพลัง** — ได้ความรู้สึก "มืออาชีพ" ทันทีและ reduce eye strain
2. **Thai font rendering บน dark background** ต้องระวัง contrast — Inter บางทีดูบางเกิน
3. **Progressive disclosure ใช้ได้ดี** — ชาวประมงไม่ต้องการเห็นค่า 6 scores ทีแรก เพียง FSI + zone ก็พอ

### 6.5.3 ทางวิจัย

1. **Literature review แน่น** ช่วยยืนยัน weight ของสูตร FSI ไม่ใช่ arbitrary
2. **การ cite paper อย่างครบถ้วน** สร้างความน่าเชื่อถือให้โครงการที่พยายามเข้าหาภาครัฐและ corporate partners
3. **การทำ spec-first** (requirements → design → tasks) ช่วยให้ team เข้าใจตรงกันแม้จะ asynchronous

---

## 6.6 คำขอบคุณ (Acknowledgements)

ขอบคุณ

- **ชุมชนประมงพื้นบ้าน** ในมหาชัยและระนอง ที่ให้ข้อมูลเบื้องต้นผ่าน community workshops
- **Global Fishing Watch** [1] สำหรับการเป็น open reference design
- **NOAA, NASA, และ ESA** สำหรับข้อมูลดาวเทียมฟรี
- **Supabase, Vercel, Mapbox** สำหรับ free tiers ที่ทำให้โครงการเริ่มต้นได้

---

## 6.7 คำส่งท้าย

โครงการ SIRINAPHA : Baan-Pla Link เริ่มต้นจากคำถามง่าย ๆ ว่า

> *"ทำไมชาวประมงไทยที่ออกเรือทุกวัน ถึงไม่ได้ประโยชน์จากดาวเทียมที่โคจรเหนือหัว?"*

คำตอบไม่ใช่ปัญหาทางเทคโนโลยี — ข้อมูลมีอยู่พร้อม — แต่เป็นปัญหาทางการออกแบบประสบการณ์ (experience design) ที่ยังไม่เชื่อมระหว่าง **ข้อมูลวิทยาศาสตร์** กับ **ปัญญาของชาวประมง** ได้

เอกสารฉบับนี้เป็นก้าวแรกของการเชื่อมนั้น — ด้วยภาษาของ pixel, color token, และ weighted formula ที่เราหวังว่าจะช่วยให้ชาวประมงพื้นบ้านไทยออกเรือได้ด้วยความมั่นใจมากขึ้น

> **"เรือลำเล็ก ถ้ารู้ว่าจะไปทางไหน ย่อมไปถึงปลายทางได้"** — สุภาษิตชาวเลพื้นบ้านไทย

---

**จัดทำโดย**
นายธีรทัพ ใยสูงเนิน (Teerathap Yaisungnoen)
10 พฤษภาคม 2569

---

> **บทถัดไป:** [บทที่ 7 — บรรณานุกรม](./07-references.md)
