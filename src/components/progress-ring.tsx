import { cn } from "@/lib/utils";

export function ProgressBar({ value, className }: { value: number; className?: string }) {
  return (
    <div className={cn("h-2 w-full overflow-hidden rounded-full bg-muted", className)}>
      <div className="h-full rounded-full bg-primary transition-all duration-500 ease-out" style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }} />
    </div>
  );
}

