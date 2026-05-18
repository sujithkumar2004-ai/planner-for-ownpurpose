"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";
import { motion } from "framer-motion";

type ModulePageProps = {
  title: string;
  summary: string;
  metrics: Array<{ label: string; value: string; progress?: number }>;
  actions: string[];
};

export function ModulePage({ title, summary, metrics, actions }: ModulePageProps) {
  return (
    <div className="grid gap-8 max-w-5xl mx-auto py-4">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative overflow-hidden rounded-3xl border border-white/10 bg-black/40 backdrop-blur-3xl p-8 md:p-12 shadow-2xl"
      >
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-purple-600/20 rounded-full blur-[100px] pointer-events-none" />
        <div className="relative z-10">
          <p className="text-sm font-semibold tracking-widest text-purple-400 uppercase mb-3">{summary}</p>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white">{title}</h1>
        </div>
      </motion.div>

      <motion.section 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="grid gap-6 md:grid-cols-3"
      >
        {metrics.map((metric, i) => (
          <motion.div 
            key={metric.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + i * 0.1 }}
          >
            <Card className="glass-card h-full relative group overflow-hidden border-white/5 hover:border-white/20 transition-colors">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
              <CardHeader className="pb-2 relative z-10">
                <CardTitle className="text-zinc-400 text-sm font-medium">{metric.label}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 pt-2 relative z-10">
                <p className="text-4xl font-bold tracking-tighter text-white">{metric.value}</p>
                {typeof metric.progress === "number" ? <ProgressBar value={metric.progress} className="h-1.5 bg-black/50" /> : null}
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </motion.section>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="glass-card border-white/5">
          <CardHeader className="border-b border-white/5 pb-4">
            <CardTitle className="text-lg font-semibold text-white">Operating Rules</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 pt-6">
            {actions.map((action, i) => (
              <div 
                key={i} 
                className="rounded-xl border border-white/5 bg-white/5 p-4 text-sm text-zinc-300 flex items-start gap-3 hover:bg-white/10 hover:border-white/10 transition-colors"
              >
                <div className="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.8)]" />
                <span className="leading-relaxed">{action}</span>
              </div>
            ))}
            {actions.length === 0 && (
              <div className="text-center py-6 text-zinc-500 italic">No specific rules defined.</div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}

