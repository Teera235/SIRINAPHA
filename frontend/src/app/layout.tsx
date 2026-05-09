import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SIRINAPHA: Baan-Pla Link",
  description:
    "แพลตฟอร์มเชื่อมต่อข้อมูลดาวเทียมกับชุมชนประมงพื้นบ้านในประเทศไทย",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="th">
      <body>{children}</body>
    </html>
  );
}
