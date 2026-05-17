import { exams } from "@/lib/seed-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

export default function ExamsPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Exams</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        {exams.map(([name, topics], index) => (
          <Card key={name as string}>
            <CardHeader><CardTitle>{name}</CardTitle></CardHeader>
            <CardContent className="grid gap-3">
              {(topics as string[]).map((topic, topicIndex) => (
                <div key={topic} className="grid gap-2">
                  <div className="flex justify-between text-sm"><span>{topic}</span><span>{(index + topicIndex + 2) * 4}%</span></div>
                  <ProgressBar value={(index + topicIndex + 2) * 4} />
                </div>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
