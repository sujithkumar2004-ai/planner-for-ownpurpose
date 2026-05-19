"use client";

import useSWR from "swr";
import { Loader2, TriangleAlert } from "lucide-react";

import { apiFetch, MonitoringOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function RecoveryModePage() {
  const { data, error, isLoading } = useSWR<MonitoringOverview>("/monitoring/overview", apiFetch);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Recovery API error: {error.message}</div>;
  const deadlines = data?.upcoming_deadlines ?? [];

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Recovery Mode</h1>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><TriangleAlert className="h-5 w-5" /> Backlog Pressure</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          <p className="text-3xl font-bold">{data?.missed_tasks ?? 0}</p>
          <p className="text-sm text-muted-foreground">Tasks currently overdue or missed.</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle>Upcoming Deadlines</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {deadlines.map((item) => <div key={item.id} className="rounded-md border border-border p-3 text-sm">{item.title} · {item.due_date ?? "No due date"}</div>)}
          {deadlines.length === 0 && <p className="text-sm text-muted-foreground">No upcoming unresolved deadlines.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
