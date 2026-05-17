import { ModulePage } from "@/components/module-page";

export default function RecoveryModePage() {
  return (
    <ModulePage
      title="Recovery Mode"
      summary="Forced correction when discipline score drops below 50 for two consecutive days."
      metrics={[
        { label: "Priority 1", value: "Backend", progress: 100 },
        { label: "Priority 2", value: "LLM", progress: 100 },
        { label: "Priority 3", value: "Exam Foundation", progress: 100 }
      ]}
      actions={[
        "Reduce new tasks for the next day.",
        "Lock optional tasks until recovery priorities are completed.",
        "Show RED warning and recovery dashboard.",
        "Treat silence as backlog, never as success."
      ]}
    />
  );
}

