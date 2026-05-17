import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProgressBar } from "@/components/progress-ring";

type ModulePageProps = {
  title: string;
  summary: string;
  metrics: Array<{ label: string; value: string; progress?: number }>;
  actions: string[];
};

export function ModulePage({ title, summary, metrics, actions }: ModulePageProps) {
  return (
    <div className="grid gap-5">
      <div>
        <p className="text-sm text-muted-foreground">{summary}</p>
        <h1 className="text-2xl font-semibold">{title}</h1>
      </div>
      <section className="grid gap-4 md:grid-cols-3">
        {metrics.map((metric) => (
          <Card key={metric.label}>
            <CardHeader><CardTitle>{metric.label}</CardTitle></CardHeader>
            <CardContent className="grid gap-3">
              <p className="text-2xl font-semibold">{metric.value}</p>
              {typeof metric.progress === "number" ? <ProgressBar value={metric.progress} /> : null}
            </CardContent>
          </Card>
        ))}
      </section>
      <Card>
        <CardHeader><CardTitle>Operating Rules</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          {actions.map((action) => <div key={action} className="rounded-md border p-3 text-sm">{action}</div>)}
        </CardContent>
      </Card>
    </div>
  );
}

