"use client";

import useSWR from "swr";
import { Bell, Loader2, Mail } from "lucide-react";

import { apiFetch, LifeNotification, LifeSettings } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function EmailAlertsPage() {
  const { data: settings, error: settingsError, isLoading: settingsLoading } = useSWR<LifeSettings>("/settings/life-os", apiFetch);
  const { data: notifications } = useSWR<LifeNotification[]>("/notifications/live", apiFetch);
  if (settingsLoading) return <div className="flex justify-center p-12"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>;
  if (settingsError) return <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-6 text-sm text-red-200">Email settings API error: {settingsError.message}</div>;

  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Email Alerts</h1>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Mail className="h-5 w-5" /> Notification Preferences</CardTitle></CardHeader>
        <CardContent className="grid gap-2 text-sm text-muted-foreground">
          {settings && Object.entries(settings.notification_preferences).map(([key, value]) => <p key={key}>{key.replaceAll("_", " ")}: {value ? "Enabled" : "Disabled"}</p>)}
        </CardContent>
      </Card>
      <Card>
        <CardHeader><CardTitle className="flex items-center gap-2"><Bell className="h-5 w-5" /> Current Alert Feed</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {(notifications ?? []).map((item) => <div key={item.id} className="rounded-md border border-border p-3 text-sm">{item.title}: <span className="text-muted-foreground">{item.body}</span></div>)}
          {(notifications ?? []).length === 0 && <p className="text-sm text-muted-foreground">No generated alerts right now.</p>}
        </CardContent>
      </Card>
    </div>
  );
}
