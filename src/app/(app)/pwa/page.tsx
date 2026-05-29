"use client";

import { useEffect, useState } from "react";
import useSWR from "swr";
import { Loader2, Smartphone } from "lucide-react";

import { apiFetch, MonitoringOverview } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function PwaPage() {
  const { data, error, isLoading } = useSWR<MonitoringOverview>("/monitoring/overview", apiFetch);
  const [online, setOnline] = useState(true);
  useEffect(() => {
    setOnline(navigator.onLine);
    const sync = () => setOnline(navigator.onLine);
    window.addEventListener("online", sync);
    window.addEventListener("offline", sync);
    return () => {
      window.removeEventListener("online", sync);
      window.removeEventListener("offline", sync);
    };
  }, []);
  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Mobile status API error: {error.message}</div>;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Mobile PWA</h1>
      <div className="grid gap-4 md:grid-cols-3">
        <Card><CardHeader><CardTitle>Network</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{online ? "Online" : "Offline"}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Queued Work</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{data?.today_pending_tasks ?? 0}</p></CardContent></Card>
        <Card><CardHeader><CardTitle>Focus Today</CardTitle></CardHeader><CardContent><p className="text-3xl font-bold">{data?.focus_minutes ?? 0}m</p></CardContent></Card>
      </div>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Smartphone className="h-5 w-5" /> Mobile Sync State</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">Next action: {data?.recommended_next_action || "No active task."}</CardContent>
      </Card>
    </div>
  );
}
