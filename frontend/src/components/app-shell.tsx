"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, BarChart3, CalendarDays, Download, Dumbbell, GraduationCap, Home, Mail, Moon, Plane, Server, Settings, ShieldCheck, Smartphone, TriangleAlert, Workflow, ListChecks, ZapOff } from "lucide-react";

import { cn } from "@/lib/utils";

const nav = [
  ["/dashboard", "Dashboard", Home],
  ["/daily-planner", "Daily Planner", ListChecks],
  ["/calendar", "Calendar", CalendarDays],
  ["/exams", "Exams", GraduationCap],
  ["/backend", "Backend", Server],
  ["/llm-agentic-ai", "LLM / Agentic AI", Workflow],
  ["/gym", "Gym", Dumbbell],
  ["/monk-mode", "Monk Mode", ShieldCheck],
  ["/travel-break", "Travel Break", Plane],
  ["/recovery-mode", "Recovery", Moon],
  ["/warnings", "Warnings", TriangleAlert],
  ["/analytics", "Analytics", BarChart3],
  ["/sleep", "Sleep", Moon],
  ["/anti-distraction", "Distractions", ZapOff],
  ["/notifications", "Notifications", Bell],
  ["/email-alerts", "Email Alerts", Mail],
  ["/export", "Export", Download],
  ["/pwa", "Mobile PWA", Smartphone],
  ["/settings", "Settings", Settings]
] as const;

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="app-grid min-h-screen">
      <aside className="border-r bg-card px-4 py-5">
        <Link href="/dashboard" className="mb-6 flex items-center gap-3 px-2">
          <div className="grid h-10 w-10 place-items-center rounded-md bg-primary text-sm font-bold text-primary-foreground">FP</div>
          <div>
            <p className="font-semibold">FinalPlanner</p>
            <p className="text-xs text-muted-foreground">Private Life OS</p>
          </div>
        </Link>
        <nav className="grid gap-1">
          {nav.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex min-h-10 items-center gap-3 rounded-md px-3 text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground",
                pathname === href && "bg-muted font-medium text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              <span>{label}</span>
            </Link>
          ))}
        </nav>
      </aside>
      <main className="min-w-0 p-4 sm:p-6 lg:p-8">{children}</main>
    </div>
  );
}
