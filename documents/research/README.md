# SIRINAPHA : Baan-Pla Link — Research & Development Document

> **รูปแบบ:** RIFFAI Academic Format · **เวอร์ชัน:** 1.0.0 · **วันที่:** 10 May 2026
> **ผู้จัดทำ:** Teerathap Yaisungnoen (นายธีรทัพ ใยสูงเนิน)

---

## สารบัญเอกสาร (Document Index)

| # | บท | ไฟล์ | สรุป |
|---|---|---|---|
| 0 | หน้าปก + บทคัดย่อ | [00-cover.md](./00-cover.md) | ข้อมูลปก, บทคัดย่อ, สารบัญ |
| 1 | บทนำ (Introduction) | [01-introduction.md](./01-introduction.md) | ที่มา, คำถามวิจัย, วัตถุประสงค์, ขอบเขต |
| 2 | ทฤษฎีและงานวิจัยที่เกี่ยวข้อง | [02-literature-review.md](./02-literature-review.md) | PFZ, HSI, NDVI thresholds, Blue Carbon, GFW design |
| 3 | วิธีการดำเนินงาน (Methodology) | [03-methodology.md](./03-methodology.md) | Data pipeline, สูตร FSI, UX process, V&V |
| 4 | ข้อกำหนดการออกแบบ | [04-design-specification.md](./04-design-specification.md) | Color tokens, typography, components, motion |
| 5 | แผนการพัฒนา | [05-implementation-plan.md](./05-implementation-plan.md) | 4 milestones, risk management |
| 6 | สรุปและข้อเสนอแนะ | [06-conclusion.md](./06-conclusion.md) | สิ่งที่บรรลุ, limitations, future work |
| 7 | บรรณานุกรม (References) | [07-references.md](./07-references.md) | IEEE format, 35 references |
| A | ภาคผนวก A — Data Sources | [appendix-a-data-sources.md](./appendix-a-data-sources.md) | API, authentication, attribution |
| B | ภาคผนวก B — Color Tokens | [appendix-b-color-tokens.md](./appendix-b-color-tokens.md) | สีครบทุก token, Tailwind config |

---

## วัตถุประสงค์ของเอกสาร

เอกสารฉบับนี้เป็น Research and Development (R&D) Document สำหรับ Dashboard ของแพลตฟอร์ม SIRINAPHA : Baan-Pla Link โดยมีคุณสมบัติดังนี้

- อ้างอิงงานวิจัยจากวารสารที่ผ่านการประเมินโดยผู้ทรงคุณวุฒิ (peer-reviewed) มากกว่า 35 รายการ ครอบคลุมทั้งด้าน remote sensing, fisheries science และ human-computer interaction
- ระบุ design system แบบครบวงจร ประกอบด้วย color tokens, typography, component specifications และ motion guidelines
- ให้ reference ที่สามารถ trace กลับไปยัง requirements ในระบบ specification ได้
- จัดทำตามรูปแบบ RIFFAI Academic Format สอดคล้องกับ thesis template ของ Teerathap Yaisungnoen

---

## วิธีการอ่านเอกสาร

### สำหรับนักวิจัย / อาจารย์
อ่านตามลำดับตั้งแต่บทที่ 1 ถึง 7 เพื่อให้เห็นภาพรวมครบถ้วน และให้ความสำคัญกับรายการอ้างอิงในบทที่ 7

### สำหรับผู้ออกแบบ (Designer)
ศึกษา [บทที่ 4 Design Specification](./04-design-specification.md) ร่วมกับ [ภาคผนวก B Color Tokens](./appendix-b-color-tokens.md) เป็นหลัก

### สำหรับนักพัฒนา (Developer)
ศึกษา [บทที่ 3 Methodology](./03-methodology.md), [บทที่ 5 Implementation Plan](./05-implementation-plan.md) และ [ภาคผนวก A Data Sources](./appendix-a-data-sources.md)

### สำหรับผู้มีส่วนได้ส่วนเสีย (Stakeholders)
อ่าน [หน้าปกและบทคัดย่อ](./00-cover.md) ร่วมกับ [บทที่ 6 Conclusion](./06-conclusion.md) เพียงพอต่อการทำความเข้าใจภาพรวม

---

## การเชื่อมโยงกับเอกสารอื่นในโปรเจกต์

- **Requirements (EARS format):** [`.kiro/specs/sirinapha-baan-pla-link/requirements.md`](../../.kiro/specs/sirinapha-baan-pla-link/requirements.md)
- **Design (20 correctness properties):** [`.kiro/specs/sirinapha-baan-pla-link/design.md`](../../.kiro/specs/sirinapha-baan-pla-link/design.md)
- **Tasks (implementation plan):** [`.kiro/specs/sirinapha-baan-pla-link/tasks.md`](../../.kiro/specs/sirinapha-baan-pla-link/tasks.md)
- **Architecture diagram:** [`documents/architecture.md`](../architecture.md)
- **Source code:** [`frontend/src/app/dashboard/`](../../frontend/src/app/dashboard/) และ [`backend/lambda/`](../../backend/lambda/)

---

## License & Citation

เอกสารนี้เป็นส่วนหนึ่งของโครงการ SIRINAPHA Research and Development Initiative จัดทำเพื่อสนับสนุนการศึกษาและชุมชนประมงพื้นบ้านในประเทศไทย

**การอ้างอิง (Citation):**

```
Yaisungnoen, T. (2026). SIRINAPHA : Baan-Pla Link — Research and Development Document
for a Global-Fishing-Watch-Style Fisheries Intelligence Dashboard.
SIRINAPHA Project Technical Report, Version 1.0.
```

---

<div align="center">
<sub>Copyright 2026 SIRINAPHA Project · จัดทำโดย Teerathap Yaisungnoen</sub>
</div>
