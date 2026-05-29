import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function levelClass(level: string) {
  return {
    GREEN: "border-warning-green text-warning-green",
    YELLOW: "border-warning-yellow text-warning-yellow",
    ORANGE: "border-warning-orange text-warning-orange",
    RED: "border-warning-red text-warning-red"
  }[level] ?? "border-muted-foreground text-muted-foreground";
}

