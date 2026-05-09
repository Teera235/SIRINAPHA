/**
 * Dashboard Layout — full-screen ocean platform (no outer shell)
 */

import type { Metadata, Viewport } from "next";

export const metadata: Metadata = {
  title: "SIRINAPHA — Ocean Data Platform",
  description: "แพลตฟอร์มข้อมูลดาวเทียมเพื่อชุมชนประมงพื้นบ้าน",
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
};

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
