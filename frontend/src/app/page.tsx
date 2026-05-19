import Link from "next/link";

export default function Home() {
  return (
    <main
      className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden"
      style={{ background: "linear-gradient(135deg, #020617 0%, #0a1e33 40%, #0c2844 100%)" }}
    >
      {/* Subtle grid overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Radial glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full opacity-20"
        style={{ background: "radial-gradient(circle, rgba(34,211,160,0.15) 0%, transparent 70%)" }}
      />

      {/* Content */}
      <div className="relative z-10 text-center px-6 max-w-3xl">
        {/* Logo mark */}
        <div className="mb-8 flex items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M6.5 12c.94-3.46 4.94-6 8.5-6 3.56 0 6.06 2.54 7 6" />
              <path d="M6.5 12c.94 3.46 4.94 6 8.5 6 3.56 0 6.06-2.54 7-6" />
              <circle cx="2.5" cy="12" r="1.5" fill="white" />
            </svg>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-5xl md:text-6xl font-bold text-white tracking-tight mb-4">
          SIRINAPHA
        </h1>
        <p className="text-lg md:text-xl text-slate-400 font-light tracking-wide mb-2">
          Baan-Pla Link Platform
        </p>
        <p className="text-sm md:text-base text-slate-500 max-w-xl mx-auto leading-relaxed mb-10">
          ระบบสารสนเทศภูมิศาสตร์เพื่อชุมชนประมงพื้นบ้านไทย
          เชื่อมต่อข้อมูลดาวเทียมกับดัชนีความเหมาะสมในการทำประมง
          ติดตามสุขภาพป่าชายเลน และทำนายผลผลิตสัตว์น้ำ
        </p>

        {/* CTA */}
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-8 py-3.5 bg-teal-500 hover:bg-teal-400 text-white font-semibold rounded-lg transition-all duration-200 shadow-lg shadow-teal-500/25 hover:shadow-teal-400/30 hover:-translate-y-0.5"
        >
          <span>เข้าสู่แดชบอร์ด</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </Link>

        {/* Secondary links */}
        <div className="mt-6 flex items-center justify-center gap-6 text-sm text-slate-500">
          <Link href="/dashboard/carbon" className="hover:text-teal-400 transition-colors">
            Blue Carbon MRV
          </Link>
          <span className="text-slate-700">|</span>
          <a
            href="https://github.com/Teera235/SIRINAPHA"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-teal-400 transition-colors"
          >
            GitHub
          </a>
        </div>
      </div>

      {/* Bottom stats bar */}
      <div className="absolute bottom-0 left-0 right-0 border-t border-slate-800/50 bg-slate-950/60 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-6">
            <div>
              <span className="text-slate-400 font-medium">6</span> data sources
            </div>
            <div>
              <span className="text-slate-400 font-medium">782</span> backend tests
            </div>
            <div>
              <span className="text-slate-400 font-medium">4</span> modules
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
            <span>NOAA OISST / NASA MODIS / Sentinel-2</span>
          </div>
        </div>
      </div>
    </main>
  );
}
