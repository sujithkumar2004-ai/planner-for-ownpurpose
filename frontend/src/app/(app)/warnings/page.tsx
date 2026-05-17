import { warnings } from "@/lib/seed-data";
import { levelClass } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const rules = [
  "missed backend block 2 days continuously",
  "missed LLM block 2 days continuously",
  "no gym completion for 3 weekdays",
  "no mock test for 14 days",
  "no revision for 5 days",
  "exam topic backlog above 25%",
  "travel break exceeds 14 days",
  "second travel break attempt",
  "daily completion below 60%",
  "weekly score below 70%"
];

export default function WarningsPage() {
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Warnings</h1>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader><CardTitle>Active Warnings</CardTitle></CardHeader>
          <CardContent className="grid gap-3">
            {warnings.map((warning) => <div key={warning.id} className={`rounded-md border-l-4 bg-muted/40 p-3 ${levelClass(warning.level)}`}><p className="font-semibold">{warning.level}</p><p className="text-sm text-foreground">{warning.message}</p></div>)}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Automatic Rules</CardTitle></CardHeader>
          <CardContent className="grid gap-2">
            {rules.map((rule) => <div key={rule} className="rounded-md border p-3 text-sm">{rule}</div>)}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
