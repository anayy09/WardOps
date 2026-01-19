import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatDateTime(date: Date | string): string {
  const d = typeof date === "string" ? new Date(date) : date;
  return d.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${Math.round(minutes)}m`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
}

export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    empty: "bg-status-empty",
    occupied: "bg-status-occupied",
    cleaning: "bg-status-cleaning",
    blocked: "bg-status-blocked",
    isolation: "bg-status-isolation",
  };
  return colors[status] || "bg-gray-400";
}

export function getAcuityColor(acuity: string): string {
  const colors: Record<string, string> = {
    low: "text-acuity-low",
    medium: "text-acuity-medium",
    high: "text-acuity-high",
    critical: "text-acuity-critical",
  };
  return colors[acuity] || "text-gray-400";
}

export function getAcuityBgColor(acuity: string): string {
  const colors: Record<string, string> = {
    low: "bg-acuity-low/20",
    medium: "bg-acuity-medium/20",
    high: "bg-acuity-high/20",
    critical: "bg-acuity-critical/20",
  };
  return colors[acuity] || "bg-gray-400/20";
}
