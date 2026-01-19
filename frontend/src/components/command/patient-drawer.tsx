"use client";

import { motion, AnimatePresence } from "framer-motion";
import { X, Clock, Activity, User, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePatientTrace } from "@/hooks/use-api";
import { cn, formatTime, formatDuration, getAcuityColor, getAcuityBgColor } from "@/lib/utils";

interface PatientDrawerProps {
  patientId: number;
  onClose: () => void;
}

export function PatientDrawer({ patientId, onClose }: PatientDrawerProps) {
  const { data: trace, isLoading } = usePatientTrace(patientId);

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 bg-black/50"
        onClick={onClose}
      />
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        exit={{ x: "100%" }}
        transition={{ type: "spring", damping: 20 }}
        className="fixed right-0 top-0 z-50 h-full w-96 bg-background shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {isLoading ? (
          <div className="flex h-full items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          </div>
        ) : trace ? (
          <div className="flex h-full flex-col">
            {/* Header */}
            <div className="flex items-center justify-between border-b p-4">
              <div>
                <h2 className="text-lg font-semibold">{trace.patient.name}</h2>
                <p className="text-sm text-muted-foreground">
                  MRN: {trace.patient.mrn}
                </p>
              </div>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            </div>

            {/* Patient Info */}
            <div className="border-b p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground">Age/Gender</p>
                  <p className="text-sm font-medium">
                    {trace.patient.age} / {trace.patient.gender}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Acuity</p>
                  <Badge
                    className={cn(
                      "mt-1",
                      getAcuityBgColor(trace.patient.acuity),
                      getAcuityColor(trace.patient.acuity)
                    )}
                  >
                    {trace.patient.acuity}
                  </Badge>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-muted-foreground">Chief Complaint</p>
                  <p className="text-sm font-medium">
                    {trace.patient.chief_complaint || "N/A"}
                  </p>
                </div>
              </div>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-3 gap-2 border-b p-4">
              <div className="rounded-md bg-muted p-2 text-center">
                <Clock className="mx-auto h-4 w-4 text-muted-foreground" />
                <p className="mt-1 text-xs text-muted-foreground">Total Time</p>
                <p className="text-sm font-medium">
                  {trace.metrics.total_time_minutes
                    ? formatDuration(trace.metrics.total_time_minutes)
                    : "—"}
                </p>
              </div>
              <div className="rounded-md bg-muted p-2 text-center">
                <Activity className="mx-auto h-4 w-4 text-muted-foreground" />
                <p className="mt-1 text-xs text-muted-foreground">Wait Time</p>
                <p className="text-sm font-medium">
                  {trace.metrics.wait_time_minutes
                    ? `${Math.round(trace.metrics.wait_time_minutes)}m`
                    : "—"}
                </p>
              </div>
              <div className="rounded-md bg-muted p-2 text-center">
                <User className="mx-auto h-4 w-4 text-muted-foreground" />
                <p className="mt-1 text-xs text-muted-foreground">Handoffs</p>
                <p className="text-sm font-medium">{trace.metrics.handoffs}</p>
              </div>
            </div>

            {/* Event Timeline */}
            <div className="flex-1 overflow-hidden">
              <div className="border-b p-4 pb-2">
                <h3 className="text-sm font-semibold">Event Timeline</h3>
              </div>
              <ScrollArea className="h-[calc(100%-48px)]">
                <div className="relative p-4 pl-8">
                  {/* Timeline line */}
                  <div className="absolute bottom-0 left-6 top-0 w-px bg-border" />

                  {trace.events.map((event: any, index: number) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="relative mb-4 last:mb-0"
                    >
                      {/* Timeline dot */}
                      <div
                        className={cn(
                          "absolute -left-2 top-1 h-4 w-4 rounded-full border-2 border-background",
                          getEventColor(event.event_type)
                        )}
                      />

                      <div className="ml-4">
                        <div className="flex items-center justify-between">
                          <p className="text-sm font-medium capitalize">
                            {event.event_type.replace(/_/g, " ")}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {formatTime(event.timestamp)}
                          </p>
                        </div>
                        {event.data && Object.keys(event.data).length > 0 && (
                          <div className="mt-1 text-xs text-muted-foreground">
                            {Object.entries(event.data).map(([key, value]) => (
                              <span key={key} className="mr-2">
                                {key.replace(/_/g, " ")}: {String(value)}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          </div>
        ) : (
          <div className="flex h-full items-center justify-center">
            <p className="text-muted-foreground">Patient not found</p>
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}

function getEventColor(eventType: string): string {
  const colors: Record<string, string> = {
    arrival: "bg-green-500",
    triage: "bg-blue-500",
    bed_assignment: "bg-purple-500",
    nurse_assignment: "bg-indigo-500",
    imaging_request: "bg-amber-500",
    imaging_start: "bg-amber-500",
    imaging_end: "bg-amber-500",
    discharge: "bg-gray-500",
    escalation: "bg-red-500",
    cleaning_start: "bg-yellow-500",
    cleaning_end: "bg-yellow-500",
  };
  return colors[eventType] || "bg-gray-400";
}
