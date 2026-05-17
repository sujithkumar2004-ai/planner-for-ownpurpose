import { ModulePage } from "@/components/module-page";

export default function MonkModePage() {
  return (
    <ModulePage
      title="Monk Mode Handler"
      summary="No vague goals. No fake progress. Discipline score decides the day."
      metrics={[
        { label: "Daily Minimum", value: "70/100", progress: 70 },
        { label: "Weekly Minimum", value: "75/100", progress: 75 },
        { label: "Critical Trigger", value: "< 50 x 2 days", progress: 50 }
      ]}
      actions={[
        "Backend and LLM blocks are non-negotiable.",
        "Gym is mandatory Monday-Friday.",
        "Social media and entertainment are penalty minutes.",
        "Critical two-day misses activate recovery mode automatically."
      ]}
    />
  );
}

