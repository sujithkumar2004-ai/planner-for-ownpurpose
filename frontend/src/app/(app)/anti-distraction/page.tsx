import { ModulePage } from "@/components/module-page";

export default function AntiDistractionPage() {
  return (
    <ModulePage
      title="Anti-Distraction Tracker"
      summary="Social media and entertainment are explicit penalty time."
      metrics={[
        { label: "Allowed Penalty", value: "0 min", progress: 100 },
        { label: "Score Impact", value: "-5 pts", progress: 95 },
        { label: "Logging", value: "Manual", progress: 50 }
      ]}
      actions={["Log distraction minutes by source.", "No-distraction day earns 5 score points.", "Penalty time appears in alerts and weekly review."]}
    />
  );
}

