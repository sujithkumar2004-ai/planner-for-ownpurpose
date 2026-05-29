"use client";

import useSWR from "swr";
import { useParams } from "next/navigation";
import { CalendarClock, Loader2, Target } from "lucide-react";

import { apiFetch, ExamCatalog, GeneratedTask, MockScore } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export default function ExamDetailPage() {
  const params = useParams<{ id: string }>();
  const examId = Number(params.id);
  const { data: exams, isLoading, error } = useSWR<ExamCatalog[]>("/exams/catalog", apiFetch);
  const { data: tasks } = useSWR<GeneratedTask[]>(`/generated-daily-tasks?date=${new Date().toISOString().split("T")[0]}`, apiFetch);
  const { data: mocks } = useSWR<MockScore[]>(`/mock-scores?exam_id=${examId}`, apiFetch);

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error || !exams) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Exam detail could not load.</div>;

  const exam = exams.find((item) => item.id === examId);
  if (!exam) return <div className="rounded-lg border border-white/10 bg-white/5 p-6">Exam not found.</div>;

  const topics = exam.subjects.flatMap((subject) => subject.topics.map((topic) => ({ ...topic, subject: subject.name })));
  const completion = topics.reduce((sum, topic) => sum + topic.progress_percent, 0) / Math.max(topics.length, 1);
  const mainDate = exam.dates[0];
  const examTasks = (tasks ?? []).filter((task) => task.exam_id === exam.id);

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">{exam.name}</h1>
          <p className="text-sm text-muted-foreground">{exam.description}</p>
        </div>
        {mainDate && <div className="flex items-center gap-2 text-sm text-zinc-300"><CalendarClock className="h-4 w-4" />{mainDate.exam_date} · {mainDate.status.toLowerCase()}</div>}
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card><CardHeader><CardTitle>Syllabus</CardTitle></CardHeader><CardContent><div className="mb-2 text-3xl font-semibold">{completion.toFixed(1)}%</div><ProgressBar value={completion} /></CardContent></Card>
        <Card><CardHeader><CardTitle>Today</CardTitle></CardHeader><CardContent><div className="text-3xl font-semibold">{examTasks.length}</div><p className="text-sm text-muted-foreground">generated task(s)</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Mocks</CardTitle></CardHeader><CardContent><div className="text-3xl font-semibold">{mocks?.[0] ? `${mocks[0].score}/${mocks[0].max_score}` : "None"}</div><p className="text-sm text-muted-foreground">latest score</p></CardContent></Card>
      </div>

      <Card>
        <CardHeader><CardTitle>Weak And Pending Topics</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {topics.sort((a, b) => b.weak_score - a.weak_score || a.progress_percent - b.progress_percent).slice(0, 16).map((topic) => (
            <div key={topic.id} className="grid gap-2 rounded-lg border border-white/5 bg-white/5 p-3">
              <div className="flex items-center justify-between gap-3 text-sm">
                <span>{topic.subject} / {topic.name}</span>
                <span className="text-zinc-400">{topic.progress_percent.toFixed(0)}% · weak {topic.weak_score.toFixed(0)}</span>
              </div>
              <ProgressBar value={topic.progress_percent} />
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Target className="h-4 w-4" />Today&apos;s Exam Tasks</CardTitle></CardHeader>
        <CardContent className="grid gap-2 text-sm">
          {examTasks.length ? examTasks.map((task) => <div key={task.id} className="rounded-lg bg-white/5 p-3">{task.title}<span className="ml-2 text-zinc-500">{task.estimated_minutes} min</span></div>) : <p className="text-muted-foreground">No generated tasks for this exam today.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
