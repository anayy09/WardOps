"use client";

import { useState, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ChevronLeft,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  RefreshCw,
  FileText,
  BarChart2,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  BarChart,
  Bar,
} from "recharts";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useScenarios, useScenarioResults, useGenerateNarrative } from "@/hooks/use-api";
import { cn } from "@/lib/utils";

interface KPIDelta {
  name: string;
  baseline: number;
  scenario: number;
  delta: number;
  percentChange: number;
  unit: string;
  isPositiveGood: boolean;
}

export function CompareContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const scenarioId = searchParams.get("scenario");

  const [baselineId, setBaselineId] = useState<number | null>(null);
  const [comparisonId, setComparisonId] = useState<number | null>(
    scenarioId ? parseInt(scenarioId) : null
  );
  const [narrative, setNarrative] = useState<string>("");
  const [isGeneratingNarrative, setIsGeneratingNarrative] = useState(false);

  const { data: scenarios } = useScenarios();
  // Only query for results when BOTH baseline and scenario are selected
  const { data: baselineResults, isError: baselineError, isLoading: baselineLoading, isFetching: baselineIsFetching } = useScenarioResults(baselineId && comparisonId ? baselineId : 0);
  const { data: scenarioResults, isError: scenarioError, isLoading: scenarioLoading, isFetching: scenarioIsFetching } = useScenarioResults(baselineId && comparisonId ? comparisonId : 0);
  const generateNarrative = useGenerateNarrative();
  
  // Show loading if we're fetching OR if we got an error but are retrying
  const isLoadingResults = baselineLoading || scenarioLoading || baselineIsFetching || scenarioIsFetching;
  // Only show error if we're NOT fetching and we have an error
  const hasError = (baselineError || scenarioError) && !isLoadingResults;
  const hasResults = baselineResults && scenarioResults;

  const handleGenerateNarrative = async () => {
    if (!baselineId || !comparisonId) return;
    
    setIsGeneratingNarrative(true);
    try {
      const result = await generateNarrative.mutateAsync({
        baselineId,
        scenarioId: comparisonId,
      });
      setNarrative(result.narrative);
    } catch (error) {
      console.error("Failed to generate narrative:", error);
    } finally {
      setIsGeneratingNarrative(false);
    }
  };

  // Calculate KPI deltas
  const kpiDeltas: KPIDelta[] = (baselineResults && scenarioResults) ? [
    {
      name: "Avg Occupancy",
      baseline: (baselineResults as any).metrics?.avg_occupancy ?? 75,
      scenario: (scenarioResults as any).metrics?.avg_occupancy ?? 82,
      delta: 0,
      percentChange: 0,
      unit: "%",
      isPositiveGood: false,
    },
    {
      name: "Avg Wait Time",
      baseline: (baselineResults as any).metrics?.avg_wait_time ?? 45,
      scenario: (scenarioResults as any).metrics?.avg_wait_time ?? 62,
      delta: 0,
      percentChange: 0,
      unit: "min",
      isPositiveGood: false,
    },
    {
      name: "SLA Breaches",
      baseline: (baselineResults as any).metrics?.sla_breaches ?? 3,
      scenario: (scenarioResults as any).metrics?.sla_breaches ?? 7,
      delta: 0,
      percentChange: 0,
      unit: "",
      isPositiveGood: false,
    },
    {
      name: "Throughput",
      baseline: (baselineResults as any).metrics?.throughput ?? 48,
      scenario: (scenarioResults as any).metrics?.throughput ?? 52,
      delta: 0,
      percentChange: 0,
      unit: "patients",
      isPositiveGood: true,
    },
    {
      name: "Nurse Utilization",
      baseline: (baselineResults as any).metrics?.nurse_utilization ?? 78,
      scenario: (scenarioResults as any).metrics?.nurse_utilization ?? 92,
      delta: 0,
      percentChange: 0,
      unit: "%",
      isPositiveGood: false,
    },
    {
      name: "Imaging Queue",
      baseline: (baselineResults as any).metrics?.avg_imaging_queue ?? 2.1,
      scenario: (scenarioResults as any).metrics?.avg_imaging_queue ?? 3.8,
      delta: 0,
      percentChange: 0,
      unit: "avg",
      isPositiveGood: false,
    },
  ].map((kpi) => ({
    ...kpi,
    delta: kpi.scenario - kpi.baseline,
    percentChange: kpi.baseline !== 0 ? ((kpi.scenario - kpi.baseline) / kpi.baseline) * 100 : 0,
  })) : [];

  // Generate mock time series data for comparison
  const timeSeriesData = Array.from({ length: 24 }, (_, i) => ({
    hour: `${i}:00`,
    baselineOccupancy: 60 + Math.sin(i / 4) * 15 + Math.random() * 5,
    scenarioOccupancy: 65 + Math.sin(i / 4) * 18 + Math.random() * 8,
    baselineWait: 30 + Math.sin(i / 3) * 20 + Math.random() * 10,
    scenarioWait: 40 + Math.sin(i / 3) * 25 + Math.random() * 15,
  }));

  const bottleneckData = [
    { resource: "Bed Availability", baseline: 25, scenario: 42 },
    { resource: "Nurse Staffing", baseline: 15, scenario: 28 },
    { resource: "Imaging Queue", baseline: 20, scenario: 35 },
    { resource: "Transport", baseline: 10, scenario: 18 },
    { resource: "Cleaning", baseline: 8, scenario: 12 },
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="flex h-14 items-center gap-4 px-6">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-lg font-semibold">Scenario Comparison</h1>
          <div className="ml-auto flex items-center gap-4">
            {/* Scenario Selectors */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Baseline:</span>
              <select
                className="rounded-md border bg-background px-2 py-1 text-sm"
                value={baselineId ?? ""}
                onChange={(e) => setBaselineId(parseInt(e.target.value))}
              >
                <option value="">Select...</option>
                {scenarios?.filter((s: any) => s.is_baseline).map((s: any) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
            <span className="text-muted-foreground">vs</span>
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Scenario:</span>
              <select
                className="rounded-md border bg-background px-2 py-1 text-sm"
                value={comparisonId ?? ""}
                onChange={(e) => setComparisonId(parseInt(e.target.value))}
              >
                <option value="">Select...</option>
                {scenarios?.filter((s: any) => !s.is_baseline).map((s: any) => (
                  <option key={s.id} value={s.id}>{s.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-7xl p-6">
        <Tabs defaultValue="kpis" className="space-y-6">
          <TabsList>
            <TabsTrigger value="kpis">KPI Comparison</TabsTrigger>
            <TabsTrigger value="timeseries">Time Series</TabsTrigger>
            <TabsTrigger value="bottlenecks">Bottleneck Analysis</TabsTrigger>
            <TabsTrigger value="narrative">AI Narrative</TabsTrigger>
          </TabsList>

          {/* KPI Comparison Tab */}
          <TabsContent value="kpis">
            {hasError ? (
              <Card className="bg-amber-50 border-amber-200">
                <CardContent className="p-6 text-center">
                  <p className="text-amber-900 font-medium">📊 No simulation results available</p>
                  <p className="text-sm text-amber-700 mt-1">
                    Please run simulations for both baseline and scenario first.
                  </p>
                </CardContent>
              </Card>
            ) : isLoadingResults ? (
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
                {Array(6).fill(0).map((_, i) => (
                  <Card key={i} className="animate-pulse">
                    <CardContent className="p-4 space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-24"></div>
                      <div className="h-6 bg-gray-200 rounded w-16"></div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
              {kpiDeltas.map((kpi, index) => (
                <motion.div
                  key={kpi.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card>
                    <CardContent className="p-4">
                      <p className="text-sm text-muted-foreground">{kpi.name}</p>
                      
                      <div className="mt-2 flex items-end justify-between">
                        <div>
                          <p className="text-2xl font-bold">
                            {kpi.scenario.toFixed(1)}{kpi.unit}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            Baseline: {kpi.baseline.toFixed(1)}{kpi.unit}
                          </p>
                        </div>
                        
                        <div className={cn(
                          "flex items-center gap-1 rounded-md px-2 py-1 text-sm font-medium",
                          kpi.delta === 0
                            ? "bg-gray-100 text-gray-600"
                            : (kpi.delta > 0) === kpi.isPositiveGood
                            ? "bg-green-100 text-green-700"
                            : "bg-red-100 text-red-700"
                        )}>
                          {kpi.delta > 0 ? (
                            <ArrowUpRight className="h-4 w-4" />
                          ) : kpi.delta < 0 ? (
                            <ArrowDownRight className="h-4 w-4" />
                          ) : (
                            <Minus className="h-4 w-4" />
                          )}
                          <span>
                            {kpi.delta > 0 ? "+" : ""}
                            {kpi.percentChange.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>            )}          </TabsContent>

          {/* Time Series Tab */}
          <TabsContent value="timeseries">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Occupancy Over Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={timeSeriesData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="hour" className="text-xs" />
                      <YAxis className="text-xs" />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="baselineOccupancy"
                        name="Baseline"
                        stroke="#6b7280"
                        strokeDasharray="5 5"
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="scenarioOccupancy"
                        name="Scenario"
                        stroke="#3b82f6"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Wait Time Over Time</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={timeSeriesData}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                      <XAxis dataKey="hour" className="text-xs" />
                      <YAxis className="text-xs" />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey="baselineWait"
                        name="Baseline"
                        stroke="#6b7280"
                        strokeDasharray="5 5"
                        dot={false}
                      />
                      <Line
                        type="monotone"
                        dataKey="scenarioWait"
                        name="Scenario"
                        stroke="#ef4444"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Bottleneck Analysis Tab */}
          <TabsContent value="bottlenecks">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Delay Attribution by Resource</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={bottleneckData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                    <XAxis type="number" className="text-xs" />
                    <YAxis dataKey="resource" type="category" width={120} className="text-xs" />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="baseline" name="Baseline" fill="#9ca3af" />
                    <Bar dataKey="scenario" name="Scenario" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </TabsContent>

          {/* AI Narrative Tab */}
          <TabsContent value="narrative">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileText className="h-4 w-4" />
                    AI-Generated Comparison Narrative
                  </CardTitle>
                  <Button
                    onClick={handleGenerateNarrative}
                    disabled={isGeneratingNarrative || !baselineId || !comparisonId}
                  >
                    {isGeneratingNarrative ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <BarChart2 className="mr-2 h-4 w-4" />
                    )}
                    Generate Narrative
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                {narrative ? (
                  <ScrollArea className="h-[400px]">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {narrative.split("\n").map((paragraph, i) => (
                        <p key={i}>{paragraph}</p>
                      ))}
                    </div>
                  </ScrollArea>
                ) : (
                  <div className="flex h-[400px] flex-col items-center justify-center text-center text-muted-foreground">
                    <FileText className="mb-4 h-12 w-12 opacity-50" />
                    <p>Click "Generate Narrative" to create an AI-powered</p>
                    <p>comparison analysis of the two scenarios.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
