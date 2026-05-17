import { dashboard } from "@/lib/seed-data";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function BackendPage() {
  const items = dashboard.roadmap.filter((item) => item.track === "backend");
  return (
    <div className="grid gap-5">
      <h1 className="text-2xl font-semibold">Backend Engineering</h1>
      <Card>
        <CardHeader><CardTitle>Roadmap</CardTitle></CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {items.map((item, index) => <div key={item.name} className="rounded-md border p-3 text-sm">{index + 1}. {item.name}</div>)}
        </CardContent>
      </Card>
    </div>
  );
}
