import { Plane } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function TravelBreakPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Travel Break</h1>
      <Card>
        <CardHeader><CardTitle>One-Time Travel Mode</CardTitle></CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <Input type="date" />
            <Input type="date" />
          </div>
          <Input placeholder="Reason" />
          <Button className="w-fit"><Plane className="h-4 w-4" /> Enable Travel Mode</Button>
          <div className="grid gap-2 text-sm text-muted-foreground">
            <p>Maximum duration: 14 continuous days.</p>
            <p>Travel mode keeps formula revision, reading/vocab, and journal tasks while pausing heavy backend and LLM work.</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

