import { Moon, Sun } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

export default function SettingsPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Card>
        <CardHeader><CardTitle>Profile & API</CardTitle></CardHeader>
        <CardContent className="grid gap-3">
          <Input placeholder="Name" />
          <Input placeholder="API base URL" defaultValue={process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"} />
          <div className="flex flex-wrap gap-2">
            <Button><Sun className="h-4 w-4" /> Light</Button>
            <Button className="bg-card text-foreground ring-1 ring-border"><Moon className="h-4 w-4" /> Dark</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

