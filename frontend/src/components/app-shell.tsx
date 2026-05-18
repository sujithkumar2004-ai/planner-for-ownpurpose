"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, BarChart3, CalendarDays, Download, Dumbbell, GraduationCap, Home, Mail, Moon, Plane, Server, Settings, ShieldCheck, Smartphone, TriangleAlert, Workflow, ListChecks, ZapOff, LogOut } from "lucide-react";

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
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("finalplanner_token");
    router.push("/login");
  };

  return (
    <div className="app-grid min-h-screen bg-black text-white">
      <aside className="border-r border-zinc-800 bg-zinc-950 px-4 py-5 flex flex-col h-screen sticky top-0 overflow-y-auto hidden-scrollbar">
        <div className="flex-1">
          <Link href="/dashboard" className="mb-8 flex items-center gap-3 px-2">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 text-sm font-bold text-white shadow-lg shadow-purple-500/20">FP</div>
            <div>
              <p className="font-bold tracking-tight text-zinc-100">FinalPlanner</p>
              <p className="text-[11px] font-medium uppercase tracking-wider text-zinc-500">Private Life OS</p>
            </div>
          </Link>
          <nav className="grid gap-1">
            {nav.map(([href, label, Icon]) => (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex min-h-10 items-center gap-3 rounded-xl px-3 text-sm text-zinc-400 transition-all hover:bg-zinc-900 hover:text-zinc-100",
                  pathname === href && "bg-zinc-800 font-semibold text-white shadow-inner"
                )}
              >
                <Icon className={cn("h-4 w-4", pathname === href ? "text-purple-400" : "")} />
                <span>{label}</span>
              </Link>
            ))}
          </nav>
        </div>
        
        <div className="mt-8 pt-4 border-t border-zinc-800">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-400 hover:bg-red-500/10 hover:text-red-400 transition-all"
          >
            <LogOut className="h-4 w-4" />
            <span className="font-medium">Sign Out</span>
          </button>
        </div>
      </aside>
      <main className="min-w-0 p-4 sm:p-6 lg:p-8 bg-zinc-950">{children}</main>
    </div>
  );
}
