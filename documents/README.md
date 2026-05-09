# Documentation

## Research and Development Document (RIFFAI Format)

เอกสารงานวิจัยและพัฒนาฉบับเต็ม พร้อมอ้างอิงงานวิจัยมากกว่า 35 รายการ จัดทำในรูปแบบ RIFFAI Academic

- **[`research/`](./research/README.md)** — R&D document ครบ 7 บท + 2 ภาคผนวก
  - [บทที่ 1 บทนำ](./research/01-introduction.md) · [บทที่ 2 Literature Review](./research/02-literature-review.md)
  - [บทที่ 3 Methodology](./research/03-methodology.md) · [บทที่ 4 Design Specification](./research/04-design-specification.md)
  - [บทที่ 5 Implementation Plan](./research/05-implementation-plan.md) · [บทที่ 6 Conclusion](./research/06-conclusion.md)
  - [บทที่ 7 References](./research/07-references.md)
  - [Appendix A — Data Sources](./research/appendix-a-data-sources.md) · [Appendix B — Color Tokens](./research/appendix-b-color-tokens.md)

## Architecture and Specifications

- [`architecture.md`](./architecture.md) — High-level system architecture and data flow
- [`.kiro/specs/sirinapha-baan-pla-link/`](../.kiro/specs/sirinapha-baan-pla-link/) — Full spec
  - `requirements.md` — 11 requirement groups with acceptance criteria (EARS format)
  - `design.md` — Complete technical design with ER diagram, API contracts, 20 correctness properties
  - `tasks.md` — Implementation plan broken into 38 tasks

## Quick Links

- [Deploy Troubleshooting](./deploy-troubleshooting.md) แก้ปัญหา CI หรือ Vercel deployment ล้มเหลว
- **Getting started**: [`../README.md`](../README.md)
- **Frontend**: [`../frontend/README.md`](../frontend/README.md)
- **Backend**: [`../backend/README.md`](../backend/README.md)
- **Database schema**: [`../supabase/migrations/`](../supabase/migrations/)

## Document Map

```
documents/
├── README.md                    — นี่ (index)
├── architecture.md              — สถาปัตยกรรมสรุปสั้น
└── research/                    — R&D document ฉบับเต็ม (RIFFAI format)
    ├── 00-cover.md              — หน้าปก + Abstract
    ├── 01-introduction.md       — บทนำ, Research Questions
    ├── 02-literature-review.md  — ทฤษฎี + paper references
    ├── 03-methodology.md        — Data pipeline, FSI formula
    ├── 04-design-specification.md  — Color tokens, components
    ├── 05-implementation-plan.md   — 4 milestones
    ├── 06-conclusion.md         — Summary + Future work
    ├── 07-references.md         — IEEE citations (35 refs)
    ├── appendix-a-data-sources.md
    └── appendix-b-color-tokens.md
```
