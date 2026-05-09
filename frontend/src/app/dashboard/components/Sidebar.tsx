"use client";

/**
 * Sidebar — เมนูด้านซ้ายสไตล์ nabha-solar (ดำ minimal)
 */

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Leaf,
  BarChart3,
  Fish,
  TreePine,
  FileText,
  Settings,
  Menu,
  X,
  Globe,
} from "lucide-react";

const NAV_ITEMS = [
  { icon: LayoutDashboard, label: "แดชบอร์ด", href: "/dashboard" },
  { icon: Fish, label: "ดัชนี FSI", href: "/dashboard#fsi" },
  { icon: Leaf, label: "ป่าชายเลน", href: "/dashboard#ndvi" },
  { icon: BarChart3, label: "ทำนายผลผลิต", href: "/dashboard#yield" },
  { icon: TreePine, label: "Blue Carbon", href: "/dashboard/carbon" },
  { icon: FileText, label: "รายงาน PDF", href: "/api/reports/pdf?type=fsi" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isExpanded, setIsExpanded] = useState(true);
  const [isMobile, setIsMobile] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const check = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) setIsExpanded(false);
    };
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  // Mobile header + overlay
  if (isMobile) {
    return (
      <>
        <div className="fixed top-0 left-0 right-0 h-14 bg-deep-black text-white z-50 flex items-center justify-between px-4">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 hover:bg-gray-800 rounded"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <h1 className="text-lg font-bold tracking-wider">
            🐟 Baan-Pla Link
          </h1>
          <div className="w-10" />
        </div>

        {mobileMenuOpen && (
          <div className="fixed inset-0 z-40 pt-14">
            <div
              className="absolute inset-0 bg-black bg-opacity-50"
              onClick={() => setMobileMenuOpen(false)}
            />
            <div className="absolute left-0 top-14 bottom-0 w-64 bg-deep-black text-white overflow-y-auto">
              <nav className="py-4">
                {NAV_ITEMS.map((item) => {
                  const active = pathname === item.href;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex items-center px-6 py-4 cursor-pointer transition-colors ${
                        active
                          ? "bg-white text-black"
                          : "hover:bg-gray-800 text-white"
                      }`}
                    >
                      <item.icon size={22} />
                      <span className="ml-4 font-medium text-base">
                        {item.label}
                      </span>
                    </Link>
                  );
                })}
              </nav>
            </div>
          </div>
        )}
      </>
    );
  }

  // Desktop sidebar
  return (
    <div
      className={`bg-deep-black text-white h-screen fixed left-0 top-0 z-50 transition-all duration-300 ${
        isExpanded ? "w-60" : "w-16"
      }`}
    >
      {/* Logo */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-center">
          {isExpanded ? (
            <h1 className="text-xl font-bold text-white tracking-wider">
              🐟 Baan-Pla Link
            </h1>
          ) : (
            <div className="w-10 h-10 bg-white rounded-sm flex items-center justify-center">
              <span className="text-black font-bold text-xl">🐟</span>
            </div>
          )}
        </div>
      </div>

      {/* Navigation */}
      <nav className="mt-8">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center px-4 py-3 cursor-pointer transition-colors ${
                active
                  ? "bg-white text-black"
                  : "hover:bg-gray-800 text-white"
              }`}
            >
              <item.icon size={20} />
              {isExpanded && (
                <span className="ml-3 font-medium">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Toggle */}
      <div className="absolute bottom-4 left-4 right-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`w-full p-2 bg-gray-800 rounded hover:bg-gray-700 transition-colors flex items-center ${
            isExpanded ? "justify-start px-4" : "justify-center"
          }`}
        >
          <LayoutDashboard size={16} />
          {isExpanded && (
            <span className="ml-2 text-sm">ย่อเมนู</span>
          )}
        </button>
      </div>
    </div>
  );
}
