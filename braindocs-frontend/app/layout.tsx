import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Space_Grotesk } from "next/font/google"; // ✅ NEW: Neo brutal font
import "./globals.css";

// ✅ ADD: Space Grotesk (main UI font)
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  weight: ["700"], // 🔥 FIX: add 900 also (bold headings)
  variable: "--font-space",
});

// ✅ EXISTING (can keep for fallback / dev use)
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// ✅ META
export const metadata: Metadata = {
  title: "BrainDocs AI",
  description: "AI RAG System",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      // 🔥 FIX: include spaceGrotesk variable
      className={`${spaceGrotesk.variable} ${geistSans.variable} ${geistMono.variable} h-full`}
    >
      {/* 🔥 FIX: apply font + full height */}
      <body className="h-full font-sans">
        {children}
      </body>
    </html>
  );
}