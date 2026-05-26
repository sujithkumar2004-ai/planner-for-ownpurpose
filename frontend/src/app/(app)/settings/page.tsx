"use client";

import useSWR from "swr";
import { Loader2, Plane, Settings } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, LifeSettings } from "@/lib/api";

export default function SettingsPage() {
  const { data, error, isLoading } = useSWR<LifeSettings>("/settings/life-os", apiFetch);

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-red-100">Settings could not be loaded from the backend.</div>;

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted-foreground">Exam selection, daily capacity, travel preferences, notifications, and date overrides are stored in the backend.</p>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Settings className="h-5 w-5" /> Selected Exams</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          {data?.selected_exams.map((plan) => (
            <div key={plan.exam_id} className="flex flex-wrap items-center justify-between gap-2 rounded-md border border-border p-3 text-sm">
              <span>{plan.exam_name}</span>
              <span className="text-muted-foreground">{plan.active ? "Active" : "Paused"} · priority {plan.priority} · {plan.available_hours_per_day}h/day · {plan.start_date} to {plan.end_date}</span>
            </div>
          ))}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Plane className="h-5 w-5" /> Travel Mode</CardTitle></CardHeader>
        <CardContent className="grid gap-2 text-sm text-muted-foreground">
          <p>Status: {data?.travel_mode.enabled ? "On" : "Off"}</p>
          <p>Dates: {data?.travel_mode.start_date ?? "not set"} to {data?.travel_mode.end_date ?? "not set"}</p>
          <p>Daily minutes: {data?.travel_mode.daily_minutes}</p>
          <p>Mock tests while travelling: {data?.travel_mode.allow_mock_tests ? "Allowed" : "Avoided"}</p>
        </CardContent>
      </Card>
    </div>
  );
}
