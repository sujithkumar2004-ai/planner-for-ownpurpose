import { Dumbbell } from "lucide-react";

import { gymRoutine } from "@/lib/seed-data";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function GymPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Gym Tracker</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Weekly Routine</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {gymRoutine.map(([day, focus]) => <div key={day} className="rounded-md border p-3"><p className="text-sm font-medium">{day}</p><p className="text-sm text-muted-foreground">{focus}</p></div>)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Log Workout</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {["exercise_name", "sets", "reps", "weight", "duration", "notes"].map((field) => <Input key={field} placeholder={field} />)}
            <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="h-5 w-5 accent-primary" /> completed</label>
            <Button><Dumbbell className="h-4 w-4" /> Save Log</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
