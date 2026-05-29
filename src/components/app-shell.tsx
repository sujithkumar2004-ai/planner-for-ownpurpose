"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Bell, BarChart3, CalendarDays, Code2, Download, Dumbbell, GraduationCap, Home, Mail, Moon, Plane, Settings, ShieldCheck, Smartphone, TriangleAlert, Workflow, ListChecks, ZapOff, LogOut } from "lucide-react";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";

const nav = [
  ["/dashboard", "Dashboard", Home],
  ["/daily-planner", "Daily Planner", ListChecks],
  ["/calendar", "Calendar", CalendarDays],
  ["/exams", "Exams", GraduationCap],
  ["/syllabus-progress", "Syllabus", BarChart3],
  ["/engineering", "Engineering", Code2],
  ["/llm-agentic-ai", "LLM / Agentic AI", Workflow],
  ["/gym", "Gym", Dumbbell],
  ["/monk-mode", "Monk Mode", ShieldCheck],
  ["/travel-mode", "Travel Mode", Plane],
  ["/comeback-mode", "Comeback", Moon],
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

const mobileNav = nav.slice(0, 5);

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    localStorage.removeItem("finalplanner_token");
    router.push("/login");
  };

  return (
    <div className="app-grid min-h-screen bg-black text-white relative selection:bg-purple-500/30">
      {/* Background ambient light */}
      <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-600/10 rounded-full blur-[120px] pointer-events-none" />
      
      <aside className="border-r border-white/5 bg-black/40 backdrop-blur-2xl px-4 py-6 flex flex-col h-screen sticky top-0 overflow-y-auto hidden-scrollbar z-10">
        <div className="flex-1">
          <Link href="/dashboard" className="mb-8 flex items-center gap-3 px-2 group">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 text-sm font-bold text-white shadow-[0_0_20px_rgba(168,85,247,0.4)] group-hover:shadow-[0_0_25px_rgba(168,85,247,0.6)] transition-all">FP</div>
            <div>
              <p className="font-bold tracking-tight text-zinc-100 group-hover:text-white transition-colors">FinalPlanner</p>
              <p className="text-[11px] font-medium uppercase tracking-widest text-zinc-500">Life OS</p>
            </div>
          </Link>
          <nav className="grid gap-1">
            {nav.map(([href, label, Icon]) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={cn(
                    "relative flex min-h-[38px] items-center gap-3 rounded-lg px-3 text-sm font-medium transition-all group",
                    isActive 
                      ? "text-white bg-white/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]" 
                      : "text-zinc-400 hover:text-zinc-100 hover:bg-white/5"
                  )}
                >
                  {isActive && (
                    <motion.div 
                      layoutId="active-nav-indicator"
                      className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-gradient-to-b from-purple-400 to-indigo-500 rounded-r-full"
                      initial={false}
                      transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    />
                  )}
                  <Icon className={cn("h-4 w-4 transition-colors", isActive ? "text-purple-400" : "group-hover:text-zinc-300")} />
                  <span>{label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
        
        <div className="mt-8 pt-4 border-t border-white/5">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-500 hover:bg-red-500/10 hover:text-red-400 transition-all font-medium group"
          >
            <LogOut className="h-4 w-4 group-hover:scale-110 transition-transform" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>
      <main className="min-w-0 p-4 pb-24 sm:p-6 lg:p-8 relative z-0">
        <div className="mx-auto max-w-7xl">
          {children}
        </div>
      </main>
      <nav className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-white/10 bg-black/90 px-2 py-2 backdrop-blur-xl lg:hidden">
        {mobileNav.map(([href, label, Icon]) => {
          const isActive = pathname === href;
          return (
            <Link key={href} href={href} className={cn("grid justify-items-center gap-1 rounded-md px-1 py-2 text-[11px]", isActive ? "text-white" : "text-zinc-500")}>
              <Icon className={cn("h-5 w-5", isActive ? "text-purple-400" : "text-zinc-500")} />
              <span className="max-w-full truncate">{label.replace("Daily Planner", "Planner")}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
