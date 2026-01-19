"use client";

import { User, AlertCircle } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { useNurses } from "@/hooks/use-api";
import { cn } from "@/lib/utils";

export function StaffingBoard() {
  const { data: nurses, isLoading } = useNurses(1);

  if (isLoading) {
    return (
      <div className="p-4">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="mt-4 space-y-2">
          {Array(4)
            .fill(0)
            .map((_, i) => (
              <div
                key={i}
                className="h-12 animate-pulse rounded bg-muted"
              />
            ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-64 flex-col">
      <div className="flex items-center justify-between border-b p-4">
        <h3 className="text-sm font-semibold">Staffing Board</h3>
        <Badge variant="secondary" className="text-xs">
          {nurses?.length || 0} nurses
        </Badge>
      </div>

      <ScrollArea className="flex-1">
        <div className="space-y-1 p-2">
          {nurses?.map((nurse) => {
            const isOverloaded = nurse.assigned_patient_count > nurse.max_patients;
            const loadPercent =
              (nurse.assigned_patient_count / nurse.max_patients) * 100;

            return (
              <div
                key={nurse.id}
                className={cn(
                  "flex items-center justify-between rounded-md p-2 transition-colors",
                  isOverloaded
                    ? "bg-red-500/10"
                    : loadPercent > 75
                    ? "bg-amber-500/10"
                    : "hover:bg-muted"
                )}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={cn(
                      "flex h-8 w-8 items-center justify-center rounded-full",
                      isOverloaded
                        ? "bg-red-500/20 text-red-500"
                        : "bg-primary/20 text-primary"
                    )}
                  >
                    <User className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{nurse.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {nurse.specialty || "General"}
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {isOverloaded && (
                    <AlertCircle className="h-4 w-4 text-red-500" />
                  )}
                  <Badge
                    variant={
                      isOverloaded
                        ? "destructive"
                        : loadPercent > 75
                        ? "warning"
                        : "secondary"
                    }
                    className="text-xs"
                  >
                    {nurse.assigned_patient_count}/{nurse.max_patients}
                  </Badge>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </div>
  );
}
