"use client";

import useSWR from "swr";
import Link from "next/link";
import { CalendarClock, Loader2, RefreshCw } from "lucide-react";

import { apiFetch, ExamCatalog } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export default function ExamsPage() {
  const { data: exams, error, mutate, isLoading } = useSWR<ExamCatalog[]>("/exams/catalog", apiFetch);

  const refreshDates = async () => {
    await apiFetch("/exams/refresh-dates", { method: "POST" });
    mutate();
  };

  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Exam data error: {error.message}</div>;
  if (isLoading || !exams) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Exams</h1>
          <p className="text-sm text-muted-foreground">Syllabus, dates, progress, and weak areas are loaded from the local planner catalog.</p>
        </div>
        <Button onClick={refreshDates}><RefreshCw className="h-4 w-4" /> Refresh official dates</Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {exams.map((exam) => {
          const topics = exam.subjects.flatMap((subject) => subject.topics);
          const completion = topics.length ? topics.reduce((sum, topic) => sum + topic.progress_percent, 0) / topics.length : 0;
          const mainDate = exam.dates[0];
          return (
            <Card key={exam.id}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between gap-3">
                  <Link href={`/exams/${exam.id}`} className="hover:text-purple-300">{exam.name}</Link>
                  {mainDate && <span className="flex items-center gap-2 text-xs font-normal text-muted-foreground"><CalendarClock className="h-4 w-4" />{mainDate.exam_date} · {mainDate.status.toLowerCase()}</span>}
                </CardTitle>
              </CardHeader>
              <CardContent className="grid gap-5">
                <div className="grid gap-2">
                  <div className="flex justify-between text-sm"><span>Syllabus completion</span><span>{completion.toFixed(1)}%</span></div>
                  <ProgressBar value={completion} />
                </div>
                {exam.subjects.map((subject) => {
                  const subjectProgress = subject.topics.length ? subject.topics.reduce((sum, topic) => sum + topic.progress_percent, 0) / subject.topics.length : 0;
                  return (
                    <div key={subject.id} className="grid gap-2 rounded-lg border border-white/5 bg-white/5 p-3">
                      <div className="flex justify-between text-sm font-medium"><span>{subject.name}</span><span>{subjectProgress.toFixed(0)}%</span></div>
                      <ProgressBar value={subjectProgress} />
                      <div className="grid gap-1">
                        {subject.topics.slice(0, 4).map((topic) => (
                          <div key={topic.id} className="flex justify-between gap-3 text-xs text-muted-foreground">
                            <span>{topic.name}</span>
                            <span>{topic.progress_percent.toFixed(0)}% · difficulty {topic.difficulty}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
