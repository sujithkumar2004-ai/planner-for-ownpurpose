"use client";

import useSWR from "swr";
import { Loader2 } from "lucide-react";

import { apiFetch, Dashboard } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LlmPage() {
  const { data, error, isLoading } = useSWR<Dashboard>("/dashboard", apiFetch);
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Roadmap API error: {error.message}</div>;
  if (isLoading || !data) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  const items = data.roadmap.filter((item) => item.track === "llm_agentic_ai");
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">LLM / Agentic AI</h1>
      <Card>
        <CardHeader><CardTitle>Roadmap</CardTitle></CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item, index) => <div key={item.name} className="rounded-md border p-3 text-sm">{index + 1}. {item.name}</div>)}
        </CardContent>
      </Card>
    </div>
  );
}
