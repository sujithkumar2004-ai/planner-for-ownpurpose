import { ModulePage } from "@/components/module-page";

export default function NotificationsPage() {
  return (
    <ModulePage
      title="Notification Center"
      summary="Warnings, recovery alerts, email events, and weekly insights in one place."
      metrics={[
        { label: "Severity", value: "GREEN-RED", progress: 80 },
        { label: "Recovery Alerts", value: "Active", progress: 90 },
        { label: "Weekly Insights", value: "Sunday", progress: 70 }
      ]}
      actions={["Surface missed mandatory blocks.", "Surface recovery-mode locks.", "Surface weekly correction day decisions."]}
    />
  );
}

