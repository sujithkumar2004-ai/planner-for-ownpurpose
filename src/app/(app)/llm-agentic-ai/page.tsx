"use client";

import useSWR from "swr";
import { Loader2, Workflow } from "lucide-react";

import { apiFetch, GeneratedTask, MonitoringOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LlmPage() {
  const { data: tasks, error, isLoading } = useSWR<GeneratedTask[]>("/api/tasks", apiFetch);
  const { data: monitoring } = useSWR<MonitoringOverview>("/monitoring/overview", apiFetch);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">LLM work API error: {error.message}</div>;
  const llmTasks = (tasks ?? []).filter((task) => /llm|agent|ai/i.test(task.title));

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">LLM / Agentic AI</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Pending Today</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.today_pending_tasks ?? 0}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Study Hours</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.study_hours ?? 0}h</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Streak</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{monitoring?.streak ?? 0}</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Workflow className="h-5 w-5" /> LLM Work From DB</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {llmTasks.map((task) => <div key={task.id} className="rounded-md border border-border p-3 text-sm">{task.title} · {task.status}</div>)}
          {llmTasks.length === 0 && <p className="text-sm text-muted-foreground">No LLM-specific tasks are currently stored for today.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
