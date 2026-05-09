"use client";

/**
 * DashboardShell — client wrapper with sidebar + main content area
 */

import Sidebar from "./Sidebar";

export default function DashboardShell({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-light-gray">
      <Sidebar />
      <main className="flex-1 ml-0 md:ml-60 pt-14 md:pt-0">
        {children}
      </main>
    </div>
  );
}
