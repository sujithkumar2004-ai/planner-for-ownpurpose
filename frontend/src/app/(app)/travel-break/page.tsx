"use client";

import { useState } from "react";
import useSWR from "swr";
import { Loader2, Plane } from "lucide-react";

import { apiFetch, TravelMode } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function TravelBreakPage() {
  const { data, error, isLoading, mutate } = useSWR<TravelMode>("/travel-mode", apiFetch);
  const [minutes, setMinutes] = useState("90");
  const [notes, setNotes] = useState("");

  const save = async () => {
    await apiFetch("/travel-mode", {
      method: "PATCH",
      body: JSON.stringify({ enabled: true, allow_mock_tests: data?.allow_mock_tests ?? false, daily_minutes: Number(minutes), notes: notes || null })
    });
    mutate();
  };

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Travel mode API error: {error.message}</div>;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Travel Break</h1>
      <Card>
        <CardHeader><CardTitle>Travel Mode</CardTitle></CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <Input type="number" min={15} max={360} value={minutes} onChange={(event) => setMinutes(event.target.value)} />
            <Input value={notes} onChange={(event) => setNotes(event.target.value)} placeholder={data?.notes ?? "Travel notes"} />
          </div>
          <Button className="w-fit" onClick={save}><Plane className="h-4 w-4" /> Enable Travel Mode</Button>
          <div className="grid gap-2 text-sm text-muted-foreground">
            <p>Status: {data?.enabled ? "On" : "Off"}</p>
            <p>Daily workload: {data?.daily_minutes ?? 0} minutes</p>
            <p>Mock tests while travelling: {data?.allow_mock_tests ? "Allowed" : "Avoided"}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
