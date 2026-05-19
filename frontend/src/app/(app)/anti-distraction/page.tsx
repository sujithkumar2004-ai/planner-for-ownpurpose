"use client";

import useSWR from "swr";
import { Loader2, ZapOff } from "lucide-react";

import { apiFetch, DistractionLog, MonitoringOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AntiDistractionPage() {
  const { data: logs, error, isLoading } = useSWR<DistractionLog[]>("/distractions/logs", apiFetch);
  const { data: monitoring } = useSWR<MonitoringOverview>("/monitoring/overview", apiFetch);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Distraction API error: {error.message}</div>;
  const totalMinutes = (logs ?? []).reduce((sum, log) => sum + log.minutes, 0);

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Anti-Distraction Tracker</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Total Logged</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{totalMinutes} min</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Productivity</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.productivity_score ?? 0}%</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Missed Tasks</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.missed_tasks ?? 0}</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><ZapOff className="h-5 w-5" /> Logs</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {(logs ?? []).map((log) => <div key={log.id} className="rounded-md border border-border p-3 text-sm">{log.log_date} · {log.source} · {log.minutes} min</div>)}
          {(logs ?? []).length === 0 && <p className="text-sm text-muted-foreground">No distraction logs in the database.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
