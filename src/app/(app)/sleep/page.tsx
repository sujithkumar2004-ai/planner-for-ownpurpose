"use client";

import useSWR from "swr";
import { Loader2, Moon } from "lucide-react";

import { apiFetch, SleepLog } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export default function SleepPage() {
  const { data, error, isLoading } = useSWR<SleepLog[]>("/sleep/logs", apiFetch);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Sleep API error: {error.message}</div>;
  const logs = data ?? [];
  const latest = logs[0];
  const averageHours = logs.length ? logs.reduce((sum, log) => sum + log.hours, 0) / logs.length : 0;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Sleep Tracker</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Latest Sleep</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{latest ? `${latest.hours}h` : "0h"}</p><p className="text-sm text-muted-foreground">{latest?.sleep_date ?? "No records"}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Average</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{averageHours.toFixed(1)}h</p><ProgressBar value={Math.min(averageHours / 8 * 100, 100)} /></CardContent></Card>
        <Card><CardHeader><CardTitle>Quality</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{latest?.quality ?? 0}/5</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Moon className="h-5 w-5" /> Sleep Logs</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {logs.map((log) => <div key={log.id} className="rounded-md border border-border p-3 text-sm">{log.sleep_date} · {log.hours}h · quality {log.quality}/5</div>)}
          {logs.length === 0 && <p className="text-sm text-muted-foreground">No sleep logs in the database.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
