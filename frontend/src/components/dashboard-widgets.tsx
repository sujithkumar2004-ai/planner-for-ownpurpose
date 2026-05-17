"use client";

import { useEffect, useState } from "react";
import { Check, Loader2, TriangleAlert } from "lucide-react";

import { apiFetch, type Dashboard } from "@/lib/api";
import { dashboard as seedDashboard } from "@/lib/seed-data";
import { levelClass } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export function DashboardWidgets() {
  const [data, setData] = useState<Dashboard>(seedDashboard);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Dashboard>("/dashboard")
      .then(setData)
      .catch(() => setData(seedDashboard))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-muted-foreground">Today</p>
          <h1 className="text-2xl font-semibold">Dashboard</h1>
        </div>
        <Button className="bg-card text-foreground ring-1 ring-border hover:bg-muted">{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Synced</Button>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader><CardTitle>Daily Completion</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <p className="text-3xl font-semibold">{data.daily_completion}%</p>
            <ProgressBar value={data.daily_completion} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Active Warnings</CardTitle></CardHeader>
          <CardContent className="flex items-center gap-3">
            <TriangleAlert className="h-7 w-7 text-warning-orange" />
            <p className="text-3xl font-semibold">{data.warnings.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Roadmap Items</CardTitle></CardHeader>
          <CardContent><p className="text-3xl font-semibold">{data.roadmap.length}</p></CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Exam Countdown</CardTitle></CardHeader>
          <CardContent className="grid gap-4">
            {data.exams.map((exam) => (
              <div key={exam.id} className="grid gap-2">
                <div className="flex items-center justify-between gap-3 text-sm">
                  <span className="font-medium">{exam.name}</span>
                  <span className="text-muted-foreground">{exam.days_left} days</span>
                </div>
                <ProgressBar value={exam.progress} />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Today&apos;s Plan</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {data.tasks.map((task) => (
              <div key={task.id} className="flex items-center justify-between gap-3 rounded-md border px-3 py-2">
                <div>
                  <p className="text-sm font-medium">{task.title}</p>
                  <p className="text-xs text-muted-foreground">{task.start_time} - {task.end_time}</p>
                </div>
                <input type="checkbox" defaultChecked={task.completed} className="h-5 w-5 accent-primary" />
              </div>
            ))}
          </CardContent>
        </Card>
      </section>

      <Card>
        <CardHeader><CardTitle>Warning Cards</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2">
          {data.warnings.map((warning) => (
            <div key={warning.id} className={`rounded-md border-l-4 bg-muted/40 p-3 ${levelClass(warning.level)}`}>
              <p className="text-sm font-semibold">{warning.level}</p>
              <p className="text-sm text-foreground">{warning.message}</p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
