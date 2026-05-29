import { FileJson, FileSpreadsheet, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiUrl } from "@/lib/api";

export default function ExportPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Export Data</h1>
      <Card>
        <CardHeader><CardTitle>Reports</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Button asChild><a href={apiUrl("/export/csv")}><FileSpreadsheet className="h-4 w-4" /> CSV</a></Button>
          <Button asChild><a href={apiUrl("/export/json")}><FileJson className="h-4 w-4" /> JSON</a></Button>
          <Button asChild><a href={apiUrl("/export/pdf")}><FileText className="h-4 w-4" /> PDF</a></Button>
        </CardContent>
      </Card>
    </div>
  );
}
