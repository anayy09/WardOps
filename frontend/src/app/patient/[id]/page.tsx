"use client";

import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ChevronLeft, Clock, Activity, User, MapPin, FileText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { usePatientTrace } from "@/hooks/use-api";
import { cn, formatTime, formatDuration, getAcuityColor, getAcuityBgColor } from "@/lib/utils";

export default function PatientPage() {
  const params = useParams();
  const router = useRouter();
  const patientId = parseInt(params.id as string);
  
  const { data: trace, isLoading } = usePatientTrace(patientId);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!trace) {
    return (
      <div className="flex h-screen flex-col items-center justify-center">
        <p className="text-lg text-muted-foreground">Patient not found</p>
        <Button variant="outline" className="mt-4" onClick={() => router.back()}>
          Go Back
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="flex h-14 items-center gap-4 px-6">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-lg font-semibold">{trace.patient.name}</h1>
            <p className="text-xs text-muted-foreground">MRN: {trace.patient.mrn}</p>
          </div>
          <Badge
            className={cn(
              "ml-4",
              getAcuityBgColor(trace.patient.acuity),
              getAcuityColor(trace.patient.acuity)
            )}
          >
            {trace.patient.acuity} Acuity
          </Badge>
        </div>
      </header>

      <main className="container mx-auto max-w-6xl p-6">
        {/* Patient Info Cards */}
        <div className="mb-6 grid grid-cols-2 gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-blue-100 p-2 dark:bg-blue-900">
                <User className="h-5 w-5 text-blue-600 dark:text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Age / Gender</p>
                <p className="font-medium">{trace.patient.age} / {trace.patient.gender}</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-amber-100 p-2 dark:bg-amber-900">
                <Clock className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Time</p>
                <p className="font-medium">
                  {trace.metrics.total_time_minutes
                    ? formatDuration(trace.metrics.total_time_minutes)
                    : "Ongoing"}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-red-100 p-2 dark:bg-red-900">
                <Activity className="h-5 w-5 text-red-600 dark:text-red-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Wait Time</p>
                <p className="font-medium">
                  {trace.metrics.wait_time_minutes
                    ? `${Math.round(trace.metrics.wait_time_minutes)}m`
                    : "—"}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="flex items-center gap-3 p-4">
              <div className="rounded-lg bg-purple-100 p-2 dark:bg-purple-900">
                <MapPin className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Handoffs</p>
                <p className="font-medium">{trace.metrics.handoffs}</p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Chief Complaint */}
        <Card className="mb-6">
          <CardHeader className="py-3">
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4" />
              Chief Complaint
            </CardTitle>
          </CardHeader>
          <CardContent className="py-2">
            <p className="text-sm">{trace.patient.chief_complaint || "Not specified"}</p>
          </CardContent>
        </Card>

        <Tabs defaultValue="timeline" className="space-y-6">
          <TabsList>
            <TabsTrigger value="timeline">Event Timeline</TabsTrigger>
            <TabsTrigger value="journey">Journey Graph</TabsTrigger>
          </TabsList>

          {/* Event Timeline Tab */}
          <TabsContent value="timeline">
            <Card>
              <CardContent className="p-6">
                <div className="relative pl-8">
                  {/* Timeline line */}
                  <div className="absolute bottom-0 left-4 top-0 w-0.5 bg-border" />

                  {trace.events.map((event: any, index: number) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="relative mb-6 last:mb-0"
                    >
                      {/* Timeline dot */}
                      <div
                        className={cn(
                          "absolute -left-4 top-1 h-4 w-4 rounded-full border-2 border-background",
                          getEventColor(event.event_type)
                        )}
                      />

                      <div className="rounded-lg border bg-card p-4 shadow-sm">
                        <div className="flex items-start justify-between">
                          <div>
                            <h3 className="font-medium capitalize">
                              {event.event_type.replace(/_/g, " ")}
                            </h3>
                            <p className="text-sm text-muted-foreground">
                              {formatTime(event.timestamp)}
                            </p>
                          </div>
                          <Badge variant="outline" className="capitalize">
                            {event.event_type.split("_")[0]}
                          </Badge>
                        </div>

                        {event.data && Object.keys(event.data).length > 0 && (
                          <div className="mt-3 grid grid-cols-2 gap-2 text-sm">
                            {Object.entries(event.data).map(([key, value]) => (
                              <div key={key}>
                                <span className="text-muted-foreground capitalize">
                                  {key.replace(/_/g, " ")}:
                                </span>{" "}
                                <span className="font-medium">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Journey Graph Tab */}
          <TabsContent value="journey">
            <Card>
              <CardContent className="p-6">
                <div className="flex flex-wrap items-center justify-center gap-4">
                  {trace.events.map((event: any, index: number) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.1 }}
                      className="flex items-center"
                    >
                      <div
                        className={cn(
                          "flex h-20 w-20 flex-col items-center justify-center rounded-lg border-2 p-2 text-center",
                          getEventBorderColor(event.event_type)
                        )}
                      >
                        <span className="text-xs font-medium capitalize leading-tight">
                          {event.event_type.replace(/_/g, " ")}
                        </span>
                        <span className="mt-1 text-[10px] text-muted-foreground">
                          {new Date(event.timestamp).toLocaleTimeString([], {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      {index < trace.events.length - 1 && (
                        <div className="mx-2 h-0.5 w-8 bg-border" />
                      )}
                    </motion.div>
                  ))}
                </div>

                {/* Journey Summary */}
                <div className="mt-8 rounded-lg bg-muted p-4">
                  <h4 className="mb-2 font-medium">Journey Summary</h4>
                  <p className="text-sm text-muted-foreground">
                    Patient arrived via {trace.events[0]?.event_type || "unknown"} and went through{" "}
                    {trace.events.length} events over{" "}
                    {trace.metrics.total_time_minutes
                      ? formatDuration(trace.metrics.total_time_minutes)
                      : "an ongoing period"}
                    . Total wait time was{" "}
                    {trace.metrics.wait_time_minutes
                      ? `${Math.round(trace.metrics.wait_time_minutes)} minutes`
                      : "not recorded"}
                    {" "}with {trace.metrics.handoffs} handoffs.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
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

function getEventBorderColor(eventType: string): string {
  const colors: Record<string, string> = {
    arrival: "border-green-500",
    triage: "border-blue-500",
    bed_assignment: "border-purple-500",
    nurse_assignment: "border-indigo-500",
    imaging_request: "border-amber-500",
    imaging_start: "border-amber-500",
    imaging_end: "border-amber-500",
    discharge: "border-gray-500",
    escalation: "border-red-500",
    cleaning_start: "border-yellow-500",
    cleaning_end: "border-yellow-500",
  };
  return colors[eventType] || "border-gray-400";
}
