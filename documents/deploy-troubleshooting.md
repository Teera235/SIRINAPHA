# Deploy Troubleshooting

แก้ไขปัญหาการ deploy และ CI ที่พบบ่อย

---

## 1. GitHub Actions ล้มเหลว: "account is locked due to a billing issue"

**อาการ** ทุก workflow run แสดงข้อความ
```
The job was not started because your account is locked due to a billing issue.
```

**สาเหตุ** Account ของคุณติด billing issue ไม่สามารถรัน Actions ได้

**วิธีแก้**

1. เปิด https://github.com/settings/billing
2. ตรวจ payment method ว่ายังใช้ได้ (บัตรไม่หมดอายุ, มียอดเพียงพอ)
3. ตรวจ spending limit ของ Actions — หากตั้งไว้ที่ $0 ให้เพิ่มเป็นค่าที่ต้องการ
4. Public repository ใช้ Actions ได้ฟรีไม่จำกัดนาที — หากยังติด ให้ลอง
   - เช็คว่ามี third-party action ที่ต้องซื้อ license หรือไม่
   - ลบ workflow run cache เก่าที่กิน storage เกิน quota
5. หลังแก้แล้ว ให้ re-run workflow

```bash
gh run rerun --repo Teera235/SIRINAPHA 25614603417
gh run rerun --repo Teera235/SIRINAPHA 25614603407
```

---

## 2. Vercel Deployment ล้มเหลว

**สาเหตุ** Vercel พยายาม build จาก root ของ repo แต่ Next.js อยู่ใน `frontend/`

**วิธีแก้** ตั้งค่า Root Directory ใน Vercel dashboard

1. เปิด https://vercel.com/dashboard แล้วเลือก project SIRINAPHA
2. ไปที่ Settings > General
3. ส่วน Root Directory กำหนดเป็น `frontend`
4. ส่วน Framework Preset ให้ Vercel detect เป็น Next.js อัตโนมัติ
5. ส่วน Build Command ใช้ค่าเริ่มต้น `next build`
6. ส่วน Install Command ใช้ค่าเริ่มต้น `npm install`
7. ส่วน Output Directory เว้นว่าง (Vercel จะใช้ `.next` ให้เอง)

**Environment Variables ที่ต้องตั้ง**

ไปที่ Settings > Environment Variables แล้วเพิ่ม

| Name | Value | Environment |
|---|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Production, Preview |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon key | Production, Preview |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase service role | Production |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox public token | Production, Preview |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API | Production |
| `LINE_CHANNEL_SECRET` | LINE webhook verify | Production |

**หลังตั้งค่าแล้ว** คลิก Redeploy ที่หน้า Deployments ล่าสุด

---

## 3. Local Build ผ่านแต่ Vercel ล้มเหลว

**สาเหตุที่พบบ่อย**

- `NEXT_PUBLIC_MAPBOX_TOKEN` ไม่ได้ตั้งใน Vercel ทำให้ build-time render ล้มเหลว
- Vercel ใช้ Node version ต่างจาก local

**วิธีแก้**

1. เพิ่ม `engines` ใน `frontend/package.json`

```json
{
  "engines": {
    "node": ">=20.x"
  }
}
```

2. ตรวจว่า environment variables ที่ขึ้นต้นด้วย `NEXT_PUBLIC_` ถูกตั้งครบในทั้ง Production และ Preview environments

3. ที่ Vercel Settings > General กำหนด Node.js Version เป็น 20.x

---

## 4. Runtime Error "Missing NEXT_PUBLIC_MAPBOX_TOKEN"

**สาเหตุ** Dashboard ต้องใช้ Mapbox token สำหรับแสดงแผนที่

**วิธีแก้ชั่วคราว (สำหรับ demo)** สร้าง token ฟรีที่ https://account.mapbox.com/access-tokens แล้วเพิ่มใน Vercel

**วิธีแก้ถาวร (Phase 2)** เปลี่ยนไปใช้ MapLibre GL JS ซึ่งเป็น open-source fork ไม่ต้องใช้ token

---

## 5. ตรวจสถานะ deploy

```bash
# GitHub Actions
gh run list --repo Teera235/SIRINAPHA --limit 5

# Vercel
vercel ls sirinapha --token $VERCEL_TOKEN
```

---

## Links

- GitHub Billing: https://github.com/settings/billing
- Vercel Dashboard: https://vercel.com/dashboard
- Mapbox Account: https://account.mapbox.com/
- Supabase Dashboard: https://supabase.com/dashboard
