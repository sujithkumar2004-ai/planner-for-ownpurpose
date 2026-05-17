import { ModulePage } from "@/components/module-page";

export default function PwaPage() {
  return (
    <ModulePage
      title="Mobile PWA"
      summary="Installable mobile Life OS with offline shell caching."
      metrics={[
        { label: "Installable", value: "Yes", progress: 100 },
        { label: "Offline Shell", value: "Enabled", progress: 85 },
        { label: "Mobile Layout", value: "Responsive", progress: 100 }
      ]}
      actions={["Manifest is served from /manifest.json.", "Service worker caches app shell assets.", "Mobile sidebar collapses into a single-column layout."]}
    />
  );
}

