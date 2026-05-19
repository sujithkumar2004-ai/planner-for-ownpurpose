"use client";

import useSWR from "swr";
import { Loader2, Server } from "lucide-react";

import { apiFetch, GeneratedTask, MonitoringOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function BackendPage() {
  const { data: tasks, error, isLoading } = useSWR<GeneratedTask[]>("/api/tasks", apiFetch);
  const { data: monitoring } = useSWR<MonitoringOverview>("/monitoring/overview", apiFetch);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Backend work API error: {error.message}</div>;
  const backendTasks = (tasks ?? []).filter((task) => task.title.toLowerCase().includes("backend"));

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Backend Engineering</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Pending Today</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.today_pending_tasks ?? 0}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Focus</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.focus_minutes ?? 0}m</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Productivity</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.productivity_score ?? 0}%</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Server className="h-5 w-5" /> Backend Work From DB</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {backendTasks.map((task) => <div key={task.id} className="rounded-md border border-border p-3 text-sm">{task.title} · {task.status}</div>)}
          {backendTasks.length === 0 && <p className="text-sm text-muted-foreground">No backend-specific tasks are currently stored for today.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
