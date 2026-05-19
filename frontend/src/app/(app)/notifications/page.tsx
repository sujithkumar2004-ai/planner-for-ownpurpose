"use client";

import useSWR from "swr";
import { Bell, Loader2 } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, LifeNotification } from "@/lib/api";

export default function NotificationsPage() {
  const { data, error, isLoading } = useSWR<LifeNotification[]>("/notifications/live", apiFetch);

  if (isLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (error) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-red-100">Notifications could not be loaded from the backend.</div>;

  return (
    <div className="grid gap-5">
      <div>
        <h1 className="text-2xl font-semibold">Notification Center</h1>
        <p className="text-sm text-muted-foreground">Daily reminders, overdue alerts, exam countdowns, and weekly review signals are generated from live Life OS data.</p>
      </div>
      <div className="grid gap-3">
        {data?.map((item) => (
          <Card key={item.id}>
            <CardHeader>
              <CardTitle className="flex items-center justify-between gap-3 text-base">
                <span className="flex items-center gap-2"><Bell className="h-4 w-4" /> {item.title}</span>
                <span className="text-xs text-muted-foreground">{item.level}</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">{item.body}</CardContent>
          </Card>
        ))}
        {data?.length === 0 && <div className="rounded-lg border border-border p-8 text-center text-sm text-muted-foreground">No active Life OS notifications.</div>}
      </div>
    </div>
  );
}
