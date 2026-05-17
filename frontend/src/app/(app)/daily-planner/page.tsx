import { fixedTasks } from "@/lib/seed-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function DailyPlannerPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Daily Planner</h1>
      <Card>
        <CardHeader><CardTitle>Fixed Schedule</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          {fixedTasks.map((task) => (
            <label key={task.id} className="flex items-center gap-3 rounded-md border p-3">
              <input type="checkbox" defaultChecked={task.completed} className="h-5 w-5 accent-primary" />
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium">{task.title}</span>
                <span className="block text-xs text-muted-foreground">{task.start_time} - {task.end_time}</span>
              </span>
            </label>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
