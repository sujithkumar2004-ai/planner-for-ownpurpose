import { ModulePage } from "@/components/module-page";

export default function SleepPage() {
  return (
    <ModulePage
      title="Sleep Tracker"
      summary="Sleep below six hours for three days becomes a RED warning."
      metrics={[
        { label: "Target", value: "6+ hours", progress: 75 },
        { label: "Quality", value: "1-5 scale", progress: 60 },
        { label: "Warning", value: "3 low days", progress: 30 }
      ]}
      actions={["Track sleep start and end.", "Record hours and quality.", "Feed sleep target into the daily discipline score."]}
    />
  );
}

