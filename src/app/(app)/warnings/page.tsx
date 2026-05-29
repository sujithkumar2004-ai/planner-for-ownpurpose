"use client";

import useSWR from "swr";
import { Loader2 } from "lucide-react";

import { apiFetch, LifeNotification } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function WarningsPage() {
  const { data, error, isLoading } = useSWR<LifeNotification[]>("/notifications/live", apiFetch);

  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Warnings API error: {error.message}</div>;
  if (isLoading || !data) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Warnings</h1>
      <Card>
        <CardHeader><CardTitle>Active Warnings</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          {data.map((warning) => <div key={warning.id} className="rounded-md border-l-4 border-orange-400 bg-muted/40 p-3"><p className="font-semibold">{warning.level}</p><p className="text-sm text-foreground">{warning.body}</p></div>)}
          {data.length === 0 && <p className="text-sm text-muted-foreground">No active warnings.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
