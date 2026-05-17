import type { Metadata } from "next";
import { Providers } from "@/components/providers";
import "./globals.css";

export const metadata: Metadata = {
  title: "FinalPlanner Life OS",
  description: "Private tracker for exams, backend, LLM learning, gym, travel, warnings, and deployment.",
  manifest: "/manifest.json"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body><Providers>{children}</Providers></body>
    </html>
  );
}
