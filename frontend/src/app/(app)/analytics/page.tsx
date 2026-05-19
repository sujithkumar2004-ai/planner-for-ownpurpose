"use client";

import useSWR from "swr";
import { BarChart3, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";
import { apiFetch, LifeAnalytics } from "@/lib/api";

export default function AnalyticsPage() {
  const { data, error, isLoading } = useSWR<LifeAnalytics>("/analytics/live", apiFetch);

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-red-100">Analytics could not be loaded from the backend.</div>;

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Analytics</h1>
        <p className="text-sm text-muted-foreground">Study hours, completion, readiness, streak, and topic heatmap are calculated from database activity.</p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><BarChart3 className="h-5 w-5" /> Completion Trend</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {data?.completion_trend.map((item) => (
              <div key={item.date} className="grid gap-2">
                <div className="flex justify-between text-sm"><span>{item.date}</span><span>{item.completion}%</span></div>
                <ProgressBar value={item.completion} />
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Study Hours</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {data?.study_hours_graph.map((item) => (
              <div key={item.date} className="grid gap-2">
                <div className="flex justify-between text-sm"><span>{item.date}</span><span>{item.hours}h</span></div>
                <ProgressBar value={Math.min(item.hours / 4 * 100, 100)} />
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Exam Readiness</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          {data?.exam_readiness.map((exam) => (
            <div key={exam.exam_id} className="grid gap-2 rounded-md border border-border/60 p-3">
              <div className="flex justify-between text-sm"><span>{exam.name}</span><span>{exam.readiness_score}%</span></div>
              <ProgressBar value={exam.readiness_score} />
            </div>
          ))}
          {data?.exam_readiness.length === 0 && <p className="text-sm text-muted-foreground">Select exams to start readiness tracking.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
