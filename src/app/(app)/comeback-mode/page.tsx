"use client";

import useSWR from "swr";
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";

import { apiFetch, ComebackMode, GeneratedTask } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export default function ComebackModePage() {
  const today = new Date().toISOString().split("T")[0];
  const { data, error, isLoading, mutate } = useSWR<ComebackMode>(`/comeback-mode?date=${today}`, apiFetch);
  const { mutate: mutateTasks } = useSWR<GeneratedTask[]>(`/generated-daily-tasks?date=${today}`, apiFetch);

  const generateRecovery = async () => {
    await apiFetch(`/generated-daily-tasks/generate?date=${today}&force=true`, { method: "POST" });
    mutate();
    mutateTasks();
  };

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error || !data) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Comeback mode could not load.</div>;

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Comeback Mode</h1>
          <p className="text-sm text-muted-foreground">Recovery planning based on backlog, weak topics, and low daily score warnings.</p>
        </div>
        <Button onClick={generateRecovery}><RefreshCw className="h-4 w-4" /> Generate Recovery Tasks</Button>
      </div>

      {data.warning && (
        <div className="flex items-start gap-3 rounded-lg border border-amber-400/20 bg-amber-500/10 p-4 text-sm text-amber-100">
          <AlertTriangle className="mt-0.5 h-4 w-4" />
          <span>{data.warning}</span>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Status</CardTitle></CardHeader><CardContent><div className="text-3xl font-semibold">{data.active ? "Active" : "Stable"}</div></CardContent></Card>
        <Card><CardHeader><CardTitle>Backlog</CardTitle></CardHeader><CardContent><div className="text-3xl font-semibold">{data.backlog_tasks}</div><p className="text-sm text-muted-foreground">unfinished generated tasks</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Weak Topics</CardTitle></CardHeader><CardContent><div className="text-3xl font-semibold">{data.weak_topic_count}</div><p className="text-sm text-muted-foreground">need recovery attention</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Recovery Plan</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {data.recovery_plan.length ? data.recovery_plan.map((item) => (
            <div key={item.topic_id} className="grid gap-2 rounded-lg border border-white/5 bg-white/5 p-3">
              <div className="flex justify-between gap-3 text-sm">
                <span>{item.topic}</span>
                <span className="text-zinc-400">{item.progress}% · weak {item.weak_score}</span>
              </div>
              <ProgressBar value={item.progress} />
              <p className="text-xs text-muted-foreground">{item.action}</p>
            </div>
          )) : <p className="text-sm text-muted-foreground">No recovery topics right now.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
