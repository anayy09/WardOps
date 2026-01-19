"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Play,
  Save,
  RefreshCw,
  ChevronLeft,
  Users,
  Bed,
  Activity,
  Clock,
  Zap,
  Sparkles,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCreateScenario, useRunSimulation, useParseScenarioText } from "@/hooks/use-api";

interface ScenarioParams {
  name: string;
  arrival_multiplier: number;
  acuity_low: number;
  acuity_medium: number;
  acuity_high: number;
  beds_available: number;
  nurses_per_shift: number;
  imaging_capacity: number;
  transport_capacity: number;
}

const defaultParams: ScenarioParams = {
  name: "New Scenario",
  arrival_multiplier: 1.0,
  acuity_low: 40,
  acuity_medium: 40,
  acuity_high: 20,
  beds_available: 24,
  nurses_per_shift: 6,
  imaging_capacity: 2,
  transport_capacity: 3,
};

export default function ScenarioPage() {
  const router = useRouter();
  const [params, setParams] = useState<ScenarioParams>(defaultParams);
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [isParsing, setIsParsing] = useState(false);
  const [simulationProgress, setSimulationProgress] = useState<{ show: boolean; progress: number; message: string }>({
    show: false,
    progress: 0,
    message: "Starting simulation...",
  });

  const createScenario = useCreateScenario();
  const runSimulation = useRunSimulation();
  const parseScenarioText = useParseScenarioText();

  const handleParamChange = (key: keyof ScenarioParams, value: number | string) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleNaturalLanguageParse = async () => {
    if (!naturalLanguage.trim()) return;
    
    setIsParsing(true);
    try {
      const result = await parseScenarioText.mutateAsync(naturalLanguage);
      if (result.params) {
        setParams((prev) => ({
          ...prev,
          ...result.params,
          name: result.name || prev.name,
        }));
      }
    } catch (error) {
      console.error("Failed to parse scenario:", error);
    } finally {
      setIsParsing(false);
    }
  };

  const handleRunScenario = async () => {
    try {
      setSimulationProgress({ show: true, progress: 10, message: "Creating scenario..." });
      
      const scenario = await createScenario.mutateAsync({
        name: params.name,
        parameters: params,
        is_baseline: false,
      });
      
      setSimulationProgress({ show: true, progress: 50, message: "Queuing simulation..." });
      
      await runSimulation.mutateAsync({
        scenarioId: scenario.id,
      });
      
      setSimulationProgress({ show: true, progress: 90, message: "Simulation started! Redirecting..." });
      
      // Wait a moment before redirecting
      setTimeout(() => {
        router.push(`/compare?scenario=${scenario.id}`);
      }, 1500);
    } catch (error) {
      console.error("Failed to run scenario:", error);
      setSimulationProgress({ show: false, progress: 0, message: "" });
    }
  };

  const handleReset = () => {
    setParams(defaultParams);
    setNaturalLanguage("");
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="flex h-14 items-center gap-4 px-6">
          <Button variant="ghost" size="icon" onClick={() => router.back()}>
            <ChevronLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-lg font-semibold">Scenario Builder</h1>
          <div className="ml-auto flex items-center gap-2">
            <Button variant="outline" onClick={handleReset}>
              <RefreshCw className="mr-2 h-4 w-4" />
              Reset
            </Button>
            <Button onClick={handleRunScenario} disabled={createScenario.isPending || runSimulation.isPending}>
              {(createScenario.isPending || runSimulation.isPending) ? (
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              ) : (
                <Play className="mr-2 h-4 w-4" />
              )}
              Run Simulation
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-4xl p-6">
        <Tabs defaultValue="sliders" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="sliders">Manual Configuration</TabsTrigger>
            <TabsTrigger value="natural">Natural Language</TabsTrigger>
          </TabsList>

          {/* Manual Configuration */}
          <TabsContent value="sliders" className="space-y-6">
            {/* Scenario Name */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Scenario Name</CardTitle>
              </CardHeader>
              <CardContent>
                <Input
                  value={params.name}
                  onChange={(e) => handleParamChange("name", e.target.value)}
                  placeholder="Enter scenario name..."
                />
              </CardContent>
            </Card>

            {/* Arrival & Acuity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-4 w-4" />
                  Patient Arrivals & Acuity
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-sm font-medium">Arrival Multiplier</label>
                    <Badge variant="outline">{params.arrival_multiplier.toFixed(1)}x</Badge>
                  </div>
                  <Slider
                    value={[params.arrival_multiplier]}
                    min={0.5}
                    max={2.0}
                    step={0.1}
                    onValueChange={([v]) => handleParamChange("arrival_multiplier", v)}
                  />
                  <p className="mt-1 text-xs text-muted-foreground">
                    Multiply baseline arrival rate (1.0x = normal)
                  </p>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium">Acuity Mix (%)</label>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <div className="mb-1 flex justify-between">
                        <span className="text-xs text-green-600">Low</span>
                        <span className="text-xs">{params.acuity_low}%</span>
                      </div>
                      <Slider
                        value={[params.acuity_low]}
                        min={0}
                        max={100}
                        step={5}
                        onValueChange={([v]) => handleParamChange("acuity_low", v)}
                      />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between">
                        <span className="text-xs text-amber-600">Medium</span>
                        <span className="text-xs">{params.acuity_medium}%</span>
                      </div>
                      <Slider
                        value={[params.acuity_medium]}
                        min={0}
                        max={100}
                        step={5}
                        onValueChange={([v]) => handleParamChange("acuity_medium", v)}
                      />
                    </div>
                    <div>
                      <div className="mb-1 flex justify-between">
                        <span className="text-xs text-red-600">High</span>
                        <span className="text-xs">{params.acuity_high}%</span>
                      </div>
                      <Slider
                        value={[params.acuity_high]}
                        min={0}
                        max={100}
                        step={5}
                        onValueChange={([v]) => handleParamChange("acuity_high", v)}
                      />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Resources */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Bed className="h-4 w-4" />
                  Bed & Staffing
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-sm font-medium">Beds Available</label>
                    <Badge variant="outline">{params.beds_available}</Badge>
                  </div>
                  <Slider
                    value={[params.beds_available]}
                    min={10}
                    max={40}
                    step={1}
                    onValueChange={([v]) => handleParamChange("beds_available", v)}
                  />
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-sm font-medium">
                      <Users className="mr-1 inline h-4 w-4" />
                      Nurses per Shift
                    </label>
                    <Badge variant="outline">{params.nurses_per_shift}</Badge>
                  </div>
                  <Slider
                    value={[params.nurses_per_shift]}
                    min={2}
                    max={12}
                    step={1}
                    onValueChange={([v]) => handleParamChange("nurses_per_shift", v)}
                  />
                </div>
              </CardContent>
            </Card>

            {/* Capacity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Zap className="h-4 w-4" />
                  Resource Capacity
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-sm font-medium">Imaging Machines</label>
                    <Badge variant="outline">{params.imaging_capacity}</Badge>
                  </div>
                  <Slider
                    value={[params.imaging_capacity]}
                    min={1}
                    max={5}
                    step={1}
                    onValueChange={([v]) => handleParamChange("imaging_capacity", v)}
                  />
                </div>

                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <label className="text-sm font-medium">Transport Units</label>
                    <Badge variant="outline">{params.transport_capacity}</Badge>
                  </div>
                  <Slider
                    value={[params.transport_capacity]}
                    min={1}
                    max={6}
                    step={1}
                    onValueChange={([v]) => handleParamChange("transport_capacity", v)}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Natural Language */}
          <TabsContent value="natural" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="h-4 w-4" />
                  Describe Your Scenario
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <textarea
                  className="min-h-[120px] w-full rounded-md border bg-transparent p-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Describe the scenario in plain English, e.g., 'Flu surge with 50% more arrivals for 6 hours, add 2 extra nurses, and reduce imaging capacity by 20%'"
                  value={naturalLanguage}
                  onChange={(e) => setNaturalLanguage(e.target.value)}
                />
                <Button onClick={handleNaturalLanguageParse} disabled={isParsing || !naturalLanguage.trim()}>
                  {isParsing ? (
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="mr-2 h-4 w-4" />
                  )}
                  Parse to Parameters
                </Button>
              </CardContent>
            </Card>

            {/* Parsed Preview */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Current Parameters</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Scenario Name</span>
                    <span className="font-medium">{params.name}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Arrival Rate</span>
                    <span className="font-medium">{params.arrival_multiplier.toFixed(1)}x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Acuity Mix</span>
                    <span className="font-medium">
                      {params.acuity_low}/{params.acuity_medium}/{params.acuity_high}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Beds</span>
                    <span className="font-medium">{params.beds_available}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Nurses/Shift</span>
                    <span className="font-medium">{params.nurses_per_shift}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Imaging</span>
                    <span className="font-medium">{params.imaging_capacity}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Transport</span>
                    <span className="font-medium">{params.transport_capacity}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="flex justify-end">
              <Button onClick={handleRunScenario} disabled={createScenario.isPending || runSimulation.isPending}>
                {(createScenario.isPending || runSimulation.isPending) ? (
                  <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Play className="mr-2 h-4 w-4" />
                )}
                Run Simulation
              </Button>
            </div>
          </TabsContent>
        </Tabs>

        {/* Simulation Progress Overlay */}
        {simulationProgress.show && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="fixed inset-0 flex items-center justify-center bg-black/50 z-50"
          >
            <Card className="w-96">
              <CardContent className="p-8 space-y-6">
                <div className="space-y-2">
                  <h2 className="text-lg font-semibold">Running Simulation</h2>
                  <p className="text-sm text-muted-foreground">{simulationProgress.message}</p>
                </div>
                
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Progress</span>
                    <span className="font-medium">{simulationProgress.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <motion.div
                      className="h-full bg-blue-500 rounded-full"
                      initial={{ width: "0%" }}
                      animate={{ width: `${simulationProgress.progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>
                
                <p className="text-xs text-muted-foreground text-center">
                  Simulating 24-hour hospital operations...
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </main>
    </div>
  );
}
