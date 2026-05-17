import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

const week = [68, 72, 60, 76, 52, 80, 42];

export default function AnalyticsPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Analytics</h1>
      <Card>
        <CardHeader><CardTitle>Weekly Completion Chart</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          {week.map((value, index) => (
            <div key={index} className="grid gap-2">
              <div className="flex justify-between text-sm"><span>Day {index + 1}</span><span>{value}%</span></div>
              <ProgressBar value={value} />
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

