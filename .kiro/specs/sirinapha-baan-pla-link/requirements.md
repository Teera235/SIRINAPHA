# เอกสารข้อกำหนดความต้องการ (Requirements Document)

## บทนำ

SIRINAPHA: Baan-Pla Link เป็นแพลตฟอร์มนวัตกรรมที่เชื่อมต่อข้อมูลดาวเทียมและปัญญาประดิษฐ์ (AI) เพื่อจัดการสุขภาพป่าชายเลนและทำนายทรัพยากรประมงสำหรับชุมชนประมงพื้นบ้านขนาดเล็กในประเทศไทย แพลตฟอร์มประกอบด้วย 4 โมดูลหลัก ได้แก่ การติดตามป่าชายเลน (Mangrove Monitoring), ดัชนีความเหมาะสมในการทำประมง (Fishery Suitability Index - FSI), การทำนายผลผลิต (Yield Prediction) และการวางแผนฟื้นฟูอย่างยั่งยืน (Sustainable Restoration Planning) โดยส่งข้อมูลผ่าน Web Dashboard, LINE Messaging API และ SMS สำรอง

## อภิธานศัพท์ (Glossary)

- **ระบบติดตามป่าชายเลน (Mangrove_Monitor)**: โมดูลที่วิเคราะห์ภาพถ่ายดาวเทียม Sentinel-2 เพื่อคำนวณค่า NDVI และตรวจจับการเปลี่ยนแปลงของป่าชายเลน
- **เครื่องคำนวณ FSI (FSI_Engine)**: โมดูลที่คำนวณดัชนีความเหมาะสมในการทำประมง (Fishery Suitability Index) จากข้อมูลหลายแหล่ง
- **ระบบทำนายผลผลิต (Yield_Predictor)**: โมดูล AI ที่ทำนายปริมาณสัตว์น้ำและแนวโน้มรายได้
- **ระบบวางแผนฟื้นฟู (Restoration_Planner)**: โมดูลที่วิเคราะห์พื้นที่เหมาะสมสำหรับการปลูกป่าชายเลนใหม่
- **ระบบส่งข้อมูล (Delivery_System)**: โมดูลที่จัดส่งข้อมูลไปยังผู้ใช้ผ่าน Web Dashboard, LINE API และ SMS
- **ท่อข้อมูล (Data_Pipeline)**: ระบบดึงและประมวลผลข้อมูลดาวเทียมและข้อมูลสมุทรศาสตร์จากแหล่งข้อมูลภายนอก
- **NDVI (Normalized Difference Vegetation Index)**: ดัชนีพืชพรรณที่คำนวณจากแถบสีแดงและอินฟราเรดใกล้ของภาพถ่ายดาวเทียม ใช้วัดสุขภาพป่าชายเลน
- **SST (Sea Surface Temperature)**: อุณหภูมิผิวน้ำทะเล ดึงจาก NOAA OISST ค่าเหมาะสม 27-30°C
- **Chl-a (Chlorophyll-a)**: ความเข้มข้นคลอโรฟิลล์-เอ ดึงจาก NASA MODIS ค่าเหมาะสม 0.5-5.0 mg/m³
- **FSI (Fishery Suitability Index)**: ดัชนีความเหมาะสมในการทำประมง คำนวณจากสูตร FSI = 0.25(SST) + 0.25(Chl-a) + 0.15(Depth) + 0.10(Lunar) + 0.25(NDVI) + 0.10(Season) มีค่าระหว่าง 0-1
- **Blue Carbon MRV**: ระบบตรวจวัด รายงาน และทวนสอบ (Measurement, Reporting, Verification) สำหรับคาร์บอนเครดิตจากป่าชายเลน
- **ชาวประมงพื้นบ้าน (Fisherman)**: ผู้ใช้หลักของระบบ ชาวประมงขนาดเล็กในชุมชนชายฝั่งไทย
- **ตัวแทนชุมชน (Community_Rep)**: ผู้ใช้ที่เป็นตัวแทนชุมชน (คนรุ่นใหม่ที่ถนัดเทคโนโลยี) ใช้ Web Dashboard
- **พันธมิตรองค์กร (Corporate_Partner)**: ลูกค้า B2B เช่น Thai Union, CPF, Seafresh ที่สมัครสมาชิกเพื่อข้อมูล ESG/Blue Carbon
- **แผนที่ FSI (FSI_Map)**: แผนที่แสดงค่า FSI เป็นภาพรวมพื้นที่ทำประมง แบ่งโซนสีตามระดับความเหมาะสม
- **Sentinel-2**: ดาวเทียมของ ESA ความละเอียด 10 เมตร 13 แถบสี รอบโคจรซ้ำ 5 วัน


## ข้อกำหนดความต้องการ (Requirements)

---

### ข้อกำหนดที่ 1: การดึงและประมวลผลข้อมูลดาวเทียม (Satellite Data Pipeline)

**User Story:** ในฐานะผู้ดูแลระบบ ฉันต้องการให้ระบบดึงข้อมูลดาวเทียมจากแหล่งข้อมูลภายนอกโดยอัตโนมัติ เพื่อให้ข้อมูลพร้อมใช้งานสำหรับการวิเคราะห์อย่างต่อเนื่อง

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Data_Pipeline SHALL ดึงข้อมูล SST จาก NOAA OISST เป็นรายวัน
2. THE Data_Pipeline SHALL ดึงข้อมูล Chlorophyll-a จาก NASA MODIS เป็นรายวัน
3. THE Data_Pipeline SHALL ดึงข้อมูลภาพถ่าย NDVI จาก Sentinel-2 ทุก 5 วันตามรอบโคจรของดาวเทียม
4. THE Data_Pipeline SHALL ดึงข้อมูลความลึกท้องทะเล (Bathymetry) จาก GEBCO และจัดเก็บเป็นข้อมูลอ้างอิงคงที่
5. THE Data_Pipeline SHALL คำนวณข้อมูลข้างขึ้นข้างแรม (Lunar Phase) โดยใช้ไลบรารี ephem
6. WHEN Data_Pipeline ดึงข้อมูลสำเร็จ THE Data_Pipeline SHALL จัดเก็บข้อมูลในฐานข้อมูลพร้อมบันทึก timestamp ของการดึงข้อมูล
7. IF Data_Pipeline ไม่สามารถเชื่อมต่อแหล่งข้อมูลภายนอกได้ THEN THE Data_Pipeline SHALL บันทึก error log และลองดึงข้อมูลซ้ำอีก 3 ครั้งโดยเว้นระยะ 5 นาทีระหว่างแต่ละครั้ง
8. IF Data_Pipeline ดึงข้อมูลซ้ำครบ 3 ครั้งแล้วยังไม่สำเร็จ THEN THE Data_Pipeline SHALL ส่งการแจ้งเตือนไปยังผู้ดูแลระบบ
9. WHEN Data_Pipeline ได้รับข้อมูลดิบจากแหล่งข้อมูลภายนอก THE Data_Pipeline SHALL ตรวจสอบความถูกต้องของรูปแบบข้อมูลก่อนจัดเก็บ

---

### ข้อกำหนดที่ 2: การติดตามสุขภาพป่าชายเลน (Mangrove Health Monitoring)

**User Story:** ในฐานะตัวแทนชุมชน ฉันต้องการติดตามสุขภาพป่าชายเลนในพื้นที่ เพื่อให้สามารถตรวจจับปัญหาและดำเนินการแก้ไขได้ทันท่วงที

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. WHEN Sentinel-2 ส่งภาพถ่ายใหม่มาถึง THE Mangrove_Monitor SHALL คำนวณค่า NDVI จากแถบสีแดง (Band 4) และอินฟราเรดใกล้ (Band 8) ของภาพถ่าย Sentinel-2
2. THE Mangrove_Monitor SHALL จำแนกสุขภาพป่าชายเลนเป็น 4 ระดับ ได้แก่ สมบูรณ์ (NDVI > 0.6), ปานกลาง (NDVI 0.4-0.6), เสื่อมโทรม (NDVI 0.2-0.4) และวิกฤต (NDVI < 0.2)
3. THE Mangrove_Monitor SHALL จัดเก็บข้อมูล NDVI เป็นอนุกรมเวลา (time-series) ย้อนหลัง 3-5 ปี เพื่อวิเคราะห์แนวโน้ม
4. WHEN ค่า NDVI ของพื้นที่ใดลดลงมากกว่า 20% เมื่อเทียบกับค่าเฉลี่ย 6 เดือนก่อนหน้า THE Mangrove_Monitor SHALL สร้างการแจ้งเตือนการบุกรุก (encroachment alert) ระดับ "เตือนภัย"
5. WHEN ค่า NDVI ของพื้นที่ใดลดลงมากกว่า 40% เมื่อเทียบกับค่าเฉลี่ย 6 เดือนก่อนหน้า THE Mangrove_Monitor SHALL สร้างการแจ้งเตือนระดับ "วิกฤต"
6. THE Mangrove_Monitor SHALL ตรวจจับการเปลี่ยนแปลงพื้นที่ป่าชายเลน (Change Detection) โดยเปรียบเทียบภาพถ่ายปัจจุบันกับภาพถ่ายก่อนหน้า
7. THE Mangrove_Monitor SHALL แสดงผลแผนที่สุขภาพป่าชายเลนเป็นภาพรวมแบ่งโซนสีตามระดับ NDVI

---

### ข้อกำหนดที่ 3: การคำนวณดัชนีความเหมาะสมในการทำประมง (Fishery Suitability Index)

**User Story:** ในฐานะชาวประมงพื้นบ้าน ฉันต้องการทราบพื้นที่ที่เหมาะสมสำหรับการทำประมง เพื่อลดค่าใช้จ่ายน้ำมันเชื้อเพลิงและเพิ่มโอกาสจับสัตว์น้ำได้

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE FSI_Engine SHALL คำนวณค่า FSI โดยใช้สูตร FSI = 0.25(SST_score) + 0.25(Chl_a_score) + 0.15(Depth_score) + 0.10(Lunar_score) + 0.25(NDVI_score) + 0.10(Season_score)
2. THE FSI_Engine SHALL แปลงค่า SST ดิบเป็นคะแนน SST_score โดยค่า 27-30°C ได้คะแนน 1.0 และค่าที่ห่างจากช่วงเหมาะสมได้คะแนนลดลงเชิงเส้น
3. THE FSI_Engine SHALL แปลงค่า Chlorophyll-a ดิบเป็นคะแนน Chl_a_score โดยค่า 0.5-5.0 mg/m³ ได้คะแนน 1.0 และค่าที่ห่างจากช่วงเหมาะสมได้คะแนนลดลงเชิงเส้น
4. THE FSI_Engine SHALL แปลงค่าความลึกเป็นคะแนน Depth_score โดยค่า 5-50 เมตรได้คะแนน 1.0 สำหรับเรือประมงพื้นบ้านขนาดเล็ก
5. THE FSI_Engine SHALL คำนวณค่า Lunar_score จากข้อมูลข้างขึ้นข้างแรมโดยคืนเดือนมืดได้คะแนนสูงกว่าคืนพระจันทร์เต็มดวง
6. THE FSI_Engine SHALL คำนวณค่า Season_score จากข้อมูลฤดูกาลและข้อมูลกรมอุตุนิยมวิทยา
7. THE FSI_Engine SHALL สร้าง FSI_Map แบ่งโซนสีเป็น 3 ระดับ ได้แก่ เหมาะสมมาก (FSI > 0.7 สีเขียว), เหมาะสมปานกลาง (FSI 0.4-0.7 สีเหลือง) และไม่เหมาะสม (FSI < 0.4 สีแดง)
8. THE FSI_Engine SHALL อัปเดตค่า FSI เป็นรายวันเมื่อข้อมูล SST และ Chlorophyll-a มีการอัปเดต
9. WHEN ข้อมูลจากแหล่งใดแหล่งหนึ่งไม่พร้อมใช้งาน THE FSI_Engine SHALL คำนวณ FSI จากข้อมูลที่มีอยู่และแสดงสถานะว่าข้อมูลไม่สมบูรณ์
10. FOR ALL ค่า FSI ที่คำนวณได้ THE FSI_Engine SHALL ให้ค่าอยู่ในช่วง 0.0 ถึง 1.0 เสมอ


---

### ข้อกำหนดที่ 4: การทำนายผลผลิตสัตว์น้ำ (Yield Prediction)

**User Story:** ในฐานะชาวประมงพื้นบ้าน ฉันต้องการทราบการทำนายปริมาณสัตว์น้ำและแนวโน้มรายได้ เพื่อวางแผนการทำประมงและการเงินล่วงหน้า

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Yield_Predictor SHALL ใช้โมเดล Machine Learning ที่รับ features ได้แก่ NDVI, SST, Chl-a และข้อมูลฤดูกาล เพื่อทำนายปริมาณสัตว์น้ำ
2. THE Yield_Predictor SHALL ทำนายปริมาณสัตว์น้ำแยกตามชนิดพันธุ์สัตว์น้ำเชิงพาณิชย์หลักในพื้นที่
3. THE Yield_Predictor SHALL ทำนายแนวโน้มรายได้ล่วงหน้า 7 วันและ 30 วัน
4. THE Yield_Predictor SHALL แสดงค่าความเชื่อมั่น (confidence interval) ของการทำนายทุกครั้ง
5. WHEN มีข้อมูลผลจับจริงจากชาวประมง THE Yield_Predictor SHALL ใช้ข้อมูลดังกล่าวเพื่อปรับปรุงความแม่นยำของโมเดลอย่างต่อเนื่อง
6. THE Yield_Predictor SHALL มีค่า Hit Rate (ความแม่นยำในการทำนายพื้นที่ที่มีสัตว์น้ำ) มากกว่า 60% ตามเป้าหมาย Phase 1

---

### ข้อกำหนดที่ 5: การวางแผนฟื้นฟูป่าชายเลนอย่างยั่งยืน (Sustainable Restoration Planning)

**User Story:** ในฐานะตัวแทนชุมชนและหน่วยงานรัฐ ฉันต้องการทราบพื้นที่ที่เหมาะสมสำหรับการปลูกป่าชายเลนใหม่ เพื่อให้การฟื้นฟูมีประสิทธิภาพสูงสุดและอัตราการรอดตายสูง

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Restoration_Planner SHALL วิเคราะห์พื้นที่เหมาะสมสำหรับการปลูกป่าชายเลนใหม่โดยพิจารณาจากข้อมูล NDVI ย้อนหลัง, สภาพดิน และระดับน้ำขึ้นน้ำลง
2. THE Restoration_Planner SHALL จัดลำดับความสำคัญของพื้นที่ฟื้นฟูตามศักยภาพในการกักเก็บคาร์บอน (carbon sequestration potential)
3. THE Restoration_Planner SHALL แสดงแผนที่พื้นที่แนะนำสำหรับการปลูกป่าชายเลนพร้อมข้อมูลพื้นที่เป็นหน่วยไร่
4. THE Restoration_Planner SHALL ประเมินอัตราการรอดตายที่คาดหวังของต้นกล้าในแต่ละพื้นที่ โดยมีเป้าหมายเพิ่มจาก 45% เป็น 85%
5. WHEN มีข้อมูลการปลูกจริง THE Restoration_Planner SHALL ติดตามอัตราการรอดตายและการเจริญเติบโตของต้นกล้าผ่านข้อมูล NDVI
6. THE Restoration_Planner SHALL คำนวณปริมาณ CO2 ที่คาดว่าจะกักเก็บได้ (tCO2/ปี) สำหรับแต่ละพื้นที่ฟื้นฟู

---

### ข้อกำหนดที่ 6: ระบบส่งข้อมูลถึงผู้ใช้ (Data Delivery System)

**User Story:** ในฐานะชาวประมงพื้นบ้าน ฉันต้องการรับข้อมูลพื้นที่ทำประมงที่เหมาะสมผ่านช่องทางที่สะดวก เพื่อให้สามารถวางแผนออกเรือได้ก่อนออกทะเล

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Delivery_System SHALL แสดงข้อมูล FSI_Map, สุขภาพป่าชายเลน และการทำนายผลผลิตบน Web Dashboard สำหรับ Community_Rep
2. THE Delivery_System SHALL ส่งข้อมูลสรุป FSI ประจำวันผ่าน LINE Messaging API ไปยัง Fisherman ที่ลงทะเบียน
3. THE Delivery_System SHALL ส่งข้อมูลสรุป FSI ประจำวันผ่าน SMS ไปยัง Fisherman ที่ไม่มีสมาร์ทโฟนหรืออินเทอร์เน็ต
4. WHEN Mangrove_Monitor สร้างการแจ้งเตือนระดับ "เตือนภัย" หรือ "วิกฤต" THE Delivery_System SHALL ส่งการแจ้งเตือนไปยัง Community_Rep ผ่าน LINE และ Web Dashboard ภายใน 30 นาที
5. THE Delivery_System SHALL แสดงข้อมูลเป็นภาษาไทยและใช้ภาษาที่เข้าใจง่ายสำหรับชาวประมง
6. THE Delivery_System SHALL รองรับการแสดงผลบนอุปกรณ์มือถือ (responsive design) สำหรับ Web Dashboard
7. WHEN Fisherman ส่งข้อความตอบกลับผ่าน LINE THE Delivery_System SHALL รับข้อมูลผลจับจริงและส่งต่อไปยัง Yield_Predictor
8. IF Delivery_System ไม่สามารถส่งข้อมูลผ่าน LINE ได้ THEN THE Delivery_System SHALL ส่งข้อมูลผ่าน SMS เป็นช่องทางสำรองโดยอัตโนมัติ

---

### ข้อกำหนดที่ 7: การจัดการผู้ใช้และการลงทะเบียน (User Management)

**User Story:** ในฐานะชาวประมงพื้นบ้าน ฉันต้องการลงทะเบียนเข้าใช้ระบบได้ง่าย เพื่อเริ่มรับข้อมูลพื้นที่ทำประมงที่เหมาะสม

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Delivery_System SHALL รองรับการลงทะเบียนผู้ใช้ 3 ประเภท ได้แก่ Fisherman, Community_Rep และ Corporate_Partner
2. WHEN Fisherman ลงทะเบียนผ่าน LINE THE Delivery_System SHALL บันทึกข้อมูลพื้นที่ทำประมงหลักและช่องทางการรับข้อมูลที่ต้องการ (LINE หรือ SMS)
3. THE Delivery_System SHALL รองรับผู้ใช้ Fisherman อย่างน้อย 50 คนใน Phase 1 และขยายเป็น 500 คนใน Phase 3
4. WHEN Community_Rep เข้าสู่ระบบ Web Dashboard THE Delivery_System SHALL แสดงข้อมูลเฉพาะพื้นที่ที่ Community_Rep รับผิดชอบ
5. WHEN Corporate_Partner เข้าสู่ระบบ THE Delivery_System SHALL แสดงข้อมูล ESG report, Blue Carbon data และ Impact report ตามระดับสมาชิก (Silver หรือ Gold)

---

### ข้อกำหนดที่ 8: ระบบ Blue Carbon MRV (Measurement, Reporting, Verification)

**User Story:** ในฐานะพันธมิตรองค์กร ฉันต้องการข้อมูล Blue Carbon ที่ผ่านการตรวจวัดและทวนสอบ เพื่อใช้ในรายงาน ESG และซื้อขายคาร์บอนเครดิต

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Mangrove_Monitor SHALL คำนวณปริมาณคาร์บอนที่กักเก็บ (tCO2) จากข้อมูล NDVI และพื้นที่ป่าชายเลน
2. THE Mangrove_Monitor SHALL สร้างรายงาน Blue Carbon ประจำเดือนและประจำปีที่ประกอบด้วยพื้นที่ป่าชายเลน, ค่า NDVI เฉลี่ย และปริมาณ CO2 ที่กักเก็บ
3. THE Mangrove_Monitor SHALL จัดเก็บข้อมูลการเปลี่ยนแปลงพื้นที่ป่าชายเลนเป็นหลักฐานสำหรับกระบวนการทวนสอบ (Verification)
4. THE Delivery_System SHALL แสดงรายงาน Blue Carbon บน Web Dashboard สำหรับ Corporate_Partner ตามระดับสมาชิก
5. THE Mangrove_Monitor SHALL คำนวณส่วนแบ่งรายได้คาร์บอนเครดิตตามสัดส่วน ได้แก่ ภาคเอกชน 63%, สหกรณ์ 20% และภาครัฐ 10% โดยระบบหัก 7% เป็นค่าบริการ MRV

---

### ข้อกำหนดที่ 9: การแสดงผล Web Dashboard (Web Dashboard Display)

**User Story:** ในฐานะตัวแทนชุมชน ฉันต้องการ Dashboard ที่แสดงข้อมูลครบถ้วนและเข้าใจง่าย เพื่อสื่อสารข้อมูลให้ชาวประมงในชุมชน

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Delivery_System SHALL แสดงแผนที่ FSI แบบ interactive ที่ Community_Rep สามารถซูมเข้า-ออกและเลือกดูรายละเอียดแต่ละพื้นที่ได้
2. THE Delivery_System SHALL แสดงกราฟแนวโน้ม NDVI ย้อนหลังเป็นอนุกรมเวลา
3. THE Delivery_System SHALL แสดงข้อมูลสภาพอากาศและทะเลปัจจุบัน ได้แก่ SST, Chl-a และสถานะข้างขึ้นข้างแรม
4. THE Delivery_System SHALL แสดงสรุปการทำนายผลผลิตสัตว์น้ำพร้อมค่าความเชื่อมั่น
5. THE Delivery_System SHALL แสดงสถานะการแจ้งเตือนป่าชายเลนทั้งหมดพร้อมระดับความรุนแรง
6. THE Delivery_System SHALL รองรับการส่งออกรายงานเป็นไฟล์ PDF สำหรับ Community_Rep และ Corporate_Partner
7. THE Delivery_System SHALL โหลดหน้า Dashboard หลักภายใน 5 วินาทีบนการเชื่อมต่ออินเทอร์เน็ต 4G

---

### ข้อกำหนดที่ 10: การจัดเก็บและจัดการข้อมูล (Data Storage and Management)

**User Story:** ในฐานะผู้ดูแลระบบ ฉันต้องการให้ข้อมูลถูกจัดเก็บอย่างเป็นระบบและปลอดภัย เพื่อรองรับการวิเคราะห์และการขยายระบบในอนาคต

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE Data_Pipeline SHALL จัดเก็บข้อมูลดาวเทียมดิบและข้อมูลที่ประมวลผลแล้วแยกจากกัน
2. THE Data_Pipeline SHALL จัดเก็บข้อมูลอนุกรมเวลา NDVI, SST และ Chl-a ย้อนหลังอย่างน้อย 5 ปี
3. THE Data_Pipeline SHALL สำรองข้อมูลอัตโนมัติเป็นรายวัน
4. THE Data_Pipeline SHALL เข้ารหัสข้อมูลส่วนบุคคลของผู้ใช้ทั้งขณะจัดเก็บ (at rest) และขณะส่งผ่าน (in transit)
5. WHEN ข้อมูลเก่ากว่า 5 ปี THE Data_Pipeline SHALL ย้ายข้อมูลไปยัง cold storage เพื่อลดค่าใช้จ่าย
6. THE Data_Pipeline SHALL รองรับการ query ข้อมูลเชิงพื้นที่ (geospatial query) สำหรับการวิเคราะห์ตามพิกัดภูมิศาสตร์

---

### ข้อกำหนดที่ 11: การแยกวิเคราะห์และจัดรูปแบบข้อมูล FSI (FSI Data Parsing and Formatting)

**User Story:** ในฐานะนักพัฒนาระบบ ฉันต้องการให้ข้อมูล FSI สามารถแปลงระหว่างรูปแบบต่างๆ ได้อย่างถูกต้อง เพื่อรองรับการแลกเปลี่ยนข้อมูลกับระบบภายนอก

#### เกณฑ์การยอมรับ (Acceptance Criteria)

1. THE FSI_Engine SHALL แปลงข้อมูล FSI เป็นรูปแบบ JSON สำหรับ API response
2. THE FSI_Engine SHALL แปลงข้อมูล FSI เป็นรูปแบบ GeoJSON สำหรับการแสดงผลแผนที่
3. THE FSI_Engine SHALL จัดรูปแบบ (format) ข้อมูล FSI กลับเป็นข้อความสรุปภาษาไทยสำหรับส่งผ่าน LINE และ SMS
4. FOR ALL ข้อมูล FSI ที่ถูกต้อง การแปลงเป็น JSON แล้วแปลงกลับเป็นวัตถุ FSI SHALL ให้ผลลัพธ์เทียบเท่ากับข้อมูลต้นฉบับ (round-trip property)
5. FOR ALL ข้อมูล FSI ที่ถูกต้อง การแปลงเป็น GeoJSON แล้วแปลงกลับเป็นวัตถุ FSI SHALL ให้ผลลัพธ์เทียบเท่ากับข้อมูลต้นฉบับ (round-trip property)
6. IF FSI_Engine ได้รับข้อมูล JSON ที่มีรูปแบบไม่ถูกต้อง THEN THE FSI_Engine SHALL ส่งคืนข้อความ error ที่ระบุตำแหน่งและสาเหตุของข้อผิดพลาด