import { ModulePage } from "@/components/module-page";

export default function EmailAlertsPage() {
  return (
    <ModulePage
      title="Email Alerts"
      summary="Resend-powered accountability emails for missed blocks and weekly review."
      metrics={[
        { label: "Daily Alert", value: "11:30 PM", progress: 100 },
        { label: "Weekly Summary", value: "Sunday 9 PM", progress: 100 },
        { label: "Provider", value: "Resend", progress: 100 }
      ]}
      actions={["Daily email includes missed tasks, discipline score, warning level, and tomorrow recovery plan.", "Weekly email includes score, blocks, exam progress, gym progress, warnings, and next focus.", "Configure EMAIL_FROM, EMAIL_TO, and RESEND_API_KEY."]}
    />
  );
}

