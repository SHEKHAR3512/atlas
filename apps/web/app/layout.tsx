import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATLAS — Autonomous Trading & Learning Agent System",
  description: "Autonomous quantitative research, backtesting, paper-trading, risk-management and algorithmic execution platform for Indian equity markets.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-background text-slate-100 min-h-screen font-sans">
        {children}
      </body>
    </html>
  );
}
