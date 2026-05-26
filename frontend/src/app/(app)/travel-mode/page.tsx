"use client";

import { useState } from "react";
import useSWR from "swr";
import { Loader2, Plane, Power } from "lucide-react";

import { apiFetch, TravelMode } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function TravelModePage() {
  const today = new Date().toISOString().split("T")[0];
  const { data, error, isLoading, mutate } = useSWR<TravelMode>("/travel-mode", apiFetch);
  const [startDate, setStartDate] = useState(data?.start_date ?? today);
  const [endDate, setEndDate] = useState(data?.end_date ?? today);
  const [minutes, setMinutes] = useState(String(data?.daily_minutes ?? 90));
  const [notes, setNotes] = useState(data?.notes ?? "");

  const save = async (enabled: boolean) => {
    await apiFetch("/travel-mode", {
      method: "PATCH",
      body: JSON.stringify({ enabled, start_date: startDate, end_date: endDate, allow_mock_tests: false, daily_minutes: Number(minutes), notes: notes || null })
    });
    mutate();
  };

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Travel mode API error: {error.message}</div>;

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Travel Mode</h1>
        <p className="text-sm text-muted-foreground">Vacation dates reduce generated tasks to light revision and redistribute missed work after travel.</p>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Plane className="h-4 w-4" />Vacation Window</CardTitle></CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-3 md:grid-cols-4">
            <Input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} />
            <Input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} />
            <Input type="number" min={15} max={360} value={minutes} onChange={(event) => setMinutes(event.target.value)} />
            <Input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Notes" />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => save(true)}><Plane className="h-4 w-4" /> Enable</Button>
            <Button className="bg-white/10 text-white" onClick={() => save(false)}><Power className="h-4 w-4" /> Disable</Button>
          </div>
          <div className="grid gap-1 text-sm text-muted-foreground">
            <p>Status: {data?.enabled ? "On" : "Off"}</p>
            <p>Dates: {data?.start_date ?? "not set"} to {data?.end_date ?? "not set"}</p>
            <p>Daily travel workload: {data?.daily_minutes ?? 0} minutes</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
