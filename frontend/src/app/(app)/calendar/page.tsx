"use client";

import { useMemo, useState } from "react";
import useSWR from "swr";
import { CalendarDays, Loader2, Pencil, Plus, Trash2 } from "lucide-react";

import { apiFetch, CalendarEvent } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

const todayIso = () => new Date().toISOString().slice(0, 10);

export default function CalendarPage() {
  const [selectedDate, setSelectedDate] = useState(todayIso());
  const [title, setTitle] = useState("");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("10:00");
  const [editing, setEditing] = useState<CalendarEvent | null>(null);
  const start = `${selectedDate}T00:00:00`;
  const end = `${selectedDate}T23:59:59`;
  const { data, error, mutate, isLoading } = useSWR<CalendarEvent[]>(`/calendar-events?start=${start}&end=${end}`, apiFetch);

  const events = useMemo(() => (data ?? []).sort((a, b) => a.start_at.localeCompare(b.start_at)), [data]);

  const saveEvent = async () => {
    const payload = {
      title,
      start_at: `${selectedDate}T${startTime}:00`,
      end_at: `${selectedDate}T${endTime}:00`,
      event_type: "manual"
    };
    if (editing) {
      await apiFetch(`/calendar-events/${editing.id}`, { method: "PATCH", body: JSON.stringify(payload) });
    } else {
      await apiFetch("/calendar-events", { method: "POST", body: JSON.stringify(payload) });
    }
    setTitle("");
    setEditing(null);
    mutate();
  };

  const editEvent = (event: CalendarEvent) => {
    setEditing(event);
    setTitle(event.title);
    setStartTime(event.start_at.slice(11, 16));
    setEndTime(event.end_at.slice(11, 16));
  };

  const deleteEvent = async (event: CalendarEvent) => {
    await apiFetch(`/calendar-events/${event.id}`, { method: "DELETE" });
    mutate();
  };

  return (
    <div className="grid gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold">Calendar</h1>
          <p className="text-sm text-muted-foreground">Manual events and generated study tasks are loaded from the API.</p>
        </div>
        <Input className="w-auto" type="date" value={selectedDate} onChange={(event) => setSelectedDate(event.target.value)} />
      </div>

      <Card>
        <CardHeader><CardTitle>{editing ? "Edit event" : "Add event"}</CardTitle></CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-[1fr_auto_auto_auto]">
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Event title" />
          <Input type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} />
          <Input type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} />
          <Button onClick={saveEvent} disabled={!title.trim()}>
            {editing ? <Pencil className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
            {editing ? "Update" : "Save"}
          </Button>
        </CardContent>
      </Card>

      {error && <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-4 text-sm text-red-200">Calendar API error: {error.message}</div>}
      {isLoading && <div className="flex justify-center p-8"><Loader2 className="h-8 w-8 animate-spin text-purple-500" /></div>}

      <div className="grid gap-3">
        {events.map((event) => (
          <Card key={event.id} className={event.completed ? "opacity-60" : ""}>
            <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
              <div>
                <p className="font-medium">{event.title}</p>
                <p className="text-sm text-muted-foreground">
                  {event.start_at.slice(11, 16)}-{event.end_at.slice(11, 16)} · {event.event_type.replace("_", " ")}
                </p>
              </div>
              <div className="flex gap-2">
                {!event.generated_task_id && <Button className="bg-white/10 text-white" onClick={() => editEvent(event)}><Pencil className="h-4 w-4" /></Button>}
                {!event.generated_task_id && <Button className="bg-white/10 text-white" onClick={() => deleteEvent(event)}><Trash2 className="h-4 w-4" /></Button>}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {!isLoading && events.length === 0 && (
        <div className="rounded-lg border border-dashed p-10 text-center text-muted-foreground">
          <CalendarDays className="mx-auto mb-3 h-10 w-10 opacity-40" />
          No calendar events for this date.
        </div>
      )}
    </div>
  );
}
