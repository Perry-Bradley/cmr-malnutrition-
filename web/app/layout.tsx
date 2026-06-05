import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const geistSans = Geist({ variable: "--font-geist-sans", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Cameroon Malnutrition Atlas",
  description:
    "Predicting child stunting hotspots in Cameroon using machine learning on sub-regional health and socio-economic data. CEC 420 Data Mining project.",
};

const NAV: { href: string; label: string }[] = [
  { href: "/",              label: "Overview" },
  { href: "/hotspots",      label: "Hotspots" },
  { href: "/predict",       label: "Predictor" },
  { href: "/regression",    label: "Regression" },
  { href: "/classification",label: "Classify" },
  { href: "/clustering",    label: "Cluster" },
  { href: "/forecasts",     label: "Forecasts" },
  { href: "/hypotheses",    label: "H1–H6" },
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col">
        <header className="sticky top-0 z-30 border-b border-zinc-200/70 bg-white/80 backdrop-blur-md">
          <div className="mx-auto flex h-14 max-w-7xl items-center gap-6 px-4 sm:px-6 lg:px-8">
            <Link href="/" className="group flex items-center gap-2.5 font-semibold tracking-tight">
              <span className="relative inline-flex">
                <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-600" />
                <span className="absolute inset-0 h-2.5 w-2.5 rounded-full bg-red-600 opacity-50 animate-ping" />
              </span>
              <span className="text-zinc-900">
                Cameroon Malnutrition Atlas
              </span>
              <span className="hidden md:inline-block text-[10px] font-medium uppercase tracking-wider text-zinc-400">
                · CEC 420
              </span>
            </Link>
            <nav className="ml-auto hidden md:flex items-center gap-0.5">
              {NAV.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-md px-2.5 py-1.5 text-sm text-zinc-600 transition-colors hover:bg-zinc-100 hover:text-zinc-900"
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
          <nav className="md:hidden no-scrollbar flex items-center gap-1 overflow-x-auto px-4 pb-2 -mt-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="shrink-0 rounded-md px-2.5 py-1 text-xs text-zinc-600 hover:bg-zinc-100"
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </header>
        <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 lg:px-8 fade-up">
          {children}
        </main>
        <footer className="border-t border-zinc-200/80 bg-white">
          <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs text-zinc-500">
              <div>
                <span className="font-medium text-zinc-700">CEC 420 — Data Mining</span>
                <span className="mx-2 text-zinc-300">·</span>
                SEPO PERRY-BRADLEY DINGA (CT23A145)
                <span className="mx-2 text-zinc-300">·</span>
                University of Buea, College of Technology
              </div>
              <div>
                Real DHS data via the DHS Program API · OpenStreetMap admin boundaries
              </div>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
