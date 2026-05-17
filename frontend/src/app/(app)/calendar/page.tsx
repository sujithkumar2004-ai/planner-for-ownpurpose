import { CalendarDays } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function CalendarPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Calendar</h1>
      <Card>
        <CardHeader><CardTitle>Travel Break Selection</CardTitle></CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-[1fr_1fr_auto]">
          <Input type="date" aria-label="Start date" />
          <Input type="date" aria-label="End date" />
          <Button><CalendarDays className="h-4 w-4" /> Reserve</Button>
        </CardContent>
      </Card>
      <div className="grid grid-cols-7 gap-2 text-center text-sm">
        {Array.from({ length: 35 }, (_, index) => (
          <div key={index} className="min-h-20 rounded-md border bg-card p-2 text-left">{index + 1}</div>
        ))}
      </div>
    </div>
  );
}

