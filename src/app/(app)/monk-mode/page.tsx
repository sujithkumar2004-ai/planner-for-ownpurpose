"use client";

import useSWR from "swr";
import { Loader2, ShieldCheck } from "lucide-react";

import { apiFetch, MonitoringOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export default function MonkModePage() {
  const { data, error, isLoading } = useSWR<MonitoringOverview>("/monitoring/overview", apiFetch);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Monitoring API error: {error.message}</div>;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Monk Mode Handler</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Productivity</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{data?.productivity_score ?? 0}%</p><ProgressBar value={data?.productivity_score ?? 0} /></CardContent></Card>
        <Card><CardHeader><CardTitle>Missed Tasks</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{data?.missed_tasks ?? 0}</p><p className="text-sm text-muted-foreground">Overdue and unresolved work</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Streak</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{data?.streak ?? 0}</p><p className="text-sm text-muted-foreground">Consecutive completion signal</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><ShieldCheck className="h-5 w-5" /> Next Discipline Action</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">{data?.recommended_next_action || "No action available yet."}</CardContent>
      </Card>
    </div>
  );
}
