"use client";

import { useState } from "react";
import useSWR from "swr";
import { Dumbbell, Loader2 } from "lucide-react";

import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type GymRoutine = { id: number; weekday: number; day_name: string; focus: string; exercises: string };

export default function GymPage() {
  const { data, error, isLoading } = useSWR<GymRoutine[]>("/gym/routine", apiFetch);
  const [exercise, setExercise] = useState("");

  const saveLog = async () => {
    await apiFetch("/gym/log", {
      method: "POST",
      body: JSON.stringify({ log_date: new Date().toISOString().slice(0, 10), exercise_name: exercise || "Workout", completed: true })
    });
    setExercise("");
  };

  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Gym API error: {error.message}</div>;
  if (isLoading || !data) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Gym Tracker</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Weekly Routine</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {data.map((routine) => <div key={routine.id} className="rounded-md border p-3"><p className="text-sm font-medium">{routine.day_name}</p><p className="text-sm text-muted-foreground">{routine.focus}</p><p className="mt-1 text-xs text-muted-foreground">{routine.exercises}</p></div>)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Log Workout</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            <Input value={exercise} onChange={(event) => setExercise(event.target.value)} placeholder="exercise name" />
            <Button onClick={saveLog}><Dumbbell className="h-4 w-4" /> Save Log</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
