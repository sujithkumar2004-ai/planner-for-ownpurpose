import { FileJson, FileSpreadsheet, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ExportPage() {
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Export Data</h1>
      <Card>
        <CardHeader><CardTitle>Reports</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild><a href={`${apiBase}/export/csv`}><FileSpreadsheet className="h-4 w-4" /> CSV</a></Button>
          <Button asChild><a href={`${apiBase}/export/json`}><FileJson className="h-4 w-4" /> JSON</a></Button>
          <Button asChild><a href={`${apiBase}/export/pdf`}><FileText className="h-4 w-4" /> PDF</a></Button>
        </CardContent>
      </Card>
    </div>
  );
}
