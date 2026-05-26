"use client";

import useSWR from "swr";
import { Loader2, Save } from "lucide-react";

import { apiFetch, ExamCatalog } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ProgressBar } from "@/components/progress-ring";

export default function SyllabusProgressPage() {
  const { data: exams, isLoading, error, mutate } = useSWR<ExamCatalog[]>("/exams/catalog", apiFetch);

  const saveTopic = async (topicId: number, progress: string, weak: string) => {
    await apiFetch(`/syllabus-topics/${topicId}`, {
      method: "PATCH",
      body: JSON.stringify({ progress_percent: Number(progress), weak_score: Number(weak) })
    });
    mutate();
  };

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error || !exams) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Syllabus progress could not load.</div>;

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Syllabus Progress</h1>
        <p className="text-sm text-muted-foreground">Progress and weak scores are stored per topic and feed daily task generation.</p>
      </div>
      {exams.map((exam) => {
        const topics = exam.subjects.flatMap((subject) => subject.topics);
        const completion = topics.reduce((sum, topic) => sum + topic.progress_percent, 0) / Math.max(topics.length, 1);
        return (
          <Card key={exam.id}>
            <CardHeader><CardTitle>{exam.name} · {completion.toFixed(1)}%</CardTitle></CardHeader>
            <CardContent className="grid gap-4">
              <ProgressBar value={completion} />
              {exam.subjects.map((subject) => (
                <div key={subject.id} className="grid gap-2">
                  <h2 className="text-sm font-medium text-zinc-200">{subject.name}</h2>
                  <div className="grid gap-2 lg:grid-cols-2">
                    {subject.topics.map((topic) => (
                      <TopicRow key={topic.id} topic={topic} onSave={saveTopic} />
                    ))}
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}

function TopicRow({ topic, onSave }: { topic: ExamCatalog["subjects"][number]["topics"][number]; onSave: (topicId: number, progress: string, weak: string) => Promise<void> }) {
  return (
    <form
      className="grid grid-cols-[1fr_82px_82px_40px] items-center gap-2 rounded-lg border border-white/5 bg-white/5 p-2 text-sm"
      onSubmit={(event) => {
        event.preventDefault();
        const form = new FormData(event.currentTarget);
        onSave(topic.id, String(form.get("progress")), String(form.get("weak")));
      }}
    >
      <span className="min-w-0 truncate">{topic.name}</span>
      <Input name="progress" type="number" min={0} max={100} defaultValue={topic.progress_percent.toFixed(0)} aria-label="Progress" />
      <Input name="weak" type="number" min={0} max={100} defaultValue={topic.weak_score.toFixed(0)} aria-label="Weak score" />
      <Button className="h-10 w-10 px-0" aria-label="Save topic"><Save className="h-4 w-4" /></Button>
    </form>
  );
}
