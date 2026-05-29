import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Providers } from "@/components/providers";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "FinalPlanner Life OS",
  description: "Private frontend-only tracker for exams, learning, gym, travel, warnings, and planning.",
  manifest: "/manifest.json"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body className={`${inter.className} bg-background text-foreground antialiased min-h-screen selection:bg-purple-500/30 selection:text-purple-200`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
