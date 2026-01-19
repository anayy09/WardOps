"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Activity,
  Moon,
  Sun,
  Home,
  Search,
  Map,
  BarChart3,
  Users,
  MessageSquare,
} from "lucide-react";
import { useTheme } from "next-themes";

import { Button } from "@/components/ui/button";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FloorMap } from "@/components/command/floor-map";
import { Timeline } from "@/components/command/timeline";
import { KPICards } from "@/components/command/kpi-cards";
import { PatientFlow } from "@/components/command/patient-flow";
import { StaffingBoard } from "@/components/command/staffing-board";
import { Copilot } from "@/components/command/copilot";
import { PatientDrawer } from "@/components/command/patient-drawer";
import { CommandPalette } from "@/components/command-palette";
import { useBeds, useKPIMetrics, useDemoStatus } from "@/hooks/use-api";
import { useCommandStore } from "@/stores/command-store";

export default function CommandPage() {
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [activeTab, setActiveTab] = useState("map");
  
  const { data: status } = useDemoStatus();
  const { data: beds, isLoading: bedsLoading } = useBeds(1);
  const { data: kpis, isLoading: kpisLoading } = useKPIMetrics(1);
  
  const { selectedPatientId, setSelectedPatientId } = useCommandStore();

  useEffect(() => {
    setMounted(true);
    
    // Keyboard shortcuts are handled by CommandPalette component itself
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setSelectedPatientId(null);
      }
    };
    
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [setSelectedPatientId]);

  // Redirect if no data loaded
  useEffect(() => {
    if (status && !status.data?.is_loaded) {
      router.push("/");
    }
  }, [status, router]);

  if (!mounted) return null;

  return (
    <TooltipProvider>
      <div className="flex h-screen flex-col bg-background">
        {/* Top Navigation */}
        <header className="flex h-14 items-center justify-between border-b px-4">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 cursor-pointer" onClick={() => router.push("/")}>
              <Activity className="h-6 w-6 text-primary" />
              <span className="text-lg font-semibold">WardOps</span>
            </div>
            <span className="text-sm text-muted-foreground">|</span>
            <span className="text-sm font-medium">Command Center</span>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              className="hidden md:flex gap-2"
              onClick={() => {
                // The CommandPalette component handles Cmd+K globally
              }}
              title="Press Cmd+K to open command palette"
            >
              <Search className="h-4 w-4" />
              <span>Commands</span>
              <kbd className="ml-2 rounded bg-muted px-1.5 py-0.5 text-xs">
                ⌘K
              </kbd>
            </Button>
            
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              title="Toggle theme"
            >
              {theme === "dark" ? (
                <Sun className="h-5 w-5" />
              ) : (
                <Moon className="h-5 w-5" />
              )}
            </Button>

            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/")}
              title="Go home"
            >
              <Home className="h-5 w-5" />
            </Button>
          </div>
        </header>

        {/* Timeline & KPIs (Fixed at top) */}
        <div className="border-b bg-background p-4 space-y-3">
          <Timeline />
          <KPICards metrics={kpis} isLoading={kpisLoading} />
        </div>

        {/* Main Content with Tabs */}
        <div className="flex flex-1 overflow-hidden">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="flex flex-1 flex-col">
            {/* Tab Navigation */}
            <TabsList className="w-full justify-start rounded-none border-b bg-background px-4 h-auto">
              <TabsTrigger value="map" className="gap-2">
                <Map className="h-4 w-4" />
                <span className="hidden sm:inline">Floor Map</span>
              </TabsTrigger>
              <TabsTrigger value="flow" className="gap-2">
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">Patient Flow</span>
              </TabsTrigger>
              <TabsTrigger value="staffing" className="gap-2">
                <Users className="h-4 w-4" />
                <span className="hidden sm:inline">Staffing</span>
              </TabsTrigger>
              <TabsTrigger value="copilot" className="gap-2">
                <MessageSquare className="h-4 w-4" />
                <span className="hidden sm:inline">Copilot</span>
              </TabsTrigger>
            </TabsList>

            {/* Tab Content */}
            <div className="flex-1 overflow-hidden">
              {/* Floor Map Tab */}
              <TabsContent value="map" className="h-full p-4 data-[state=inactive]:hidden">
                <div className="h-full flex flex-col">
                  <div className="mb-3">
                    <h2 className="text-lg font-semibold">Medical Unit A - Floor Map</h2>
                    <p className="text-sm text-muted-foreground">Click on a bed to view patient details</p>
                  </div>
                  <div className="flex-1 overflow-auto">
                    <FloorMap
                      beds={beds || []}
                      isLoading={bedsLoading}
                      onBedClick={(bed) => {
                        if (bed.current_patient_id) {
                          setSelectedPatientId(bed.current_patient_id);
                        }
                      }}
                    />
                  </div>
                </div>
              </TabsContent>

              {/* Patient Flow Tab */}
              <TabsContent value="flow" className="h-full p-4 data-[state=inactive]:hidden">
                <div className="h-full flex flex-col">
                  <div className="mb-3">
                    <h2 className="text-lg font-semibold">Patient Flow & Queues</h2>
                    <p className="text-sm text-muted-foreground">Sankey diagram and queue metrics</p>
                  </div>
                  <div className="flex-1 overflow-auto">
                    <PatientFlow />
                  </div>
                </div>
              </TabsContent>

              {/* Staffing Tab */}
              <TabsContent value="staffing" className="h-full p-4 data-[state=inactive]:hidden">
                <div className="h-full flex flex-col">
                  <div className="mb-3">
                    <h2 className="text-lg font-semibold">Staffing Board</h2>
                    <p className="text-sm text-muted-foreground">Nurse assignments and capacity</p>
                  </div>
                  <div className="flex-1 overflow-auto">
                    <StaffingBoard />
                  </div>
                </div>
              </TabsContent>

              {/* Copilot Tab */}
              <TabsContent value="copilot" className="h-full p-4 data-[state=inactive]:hidden">
                <div className="h-full flex flex-col">
                  <div className="mb-3">
                    <h2 className="text-lg font-semibold">AI Operations Copilot</h2>
                    <p className="text-sm text-muted-foreground">Ask about operations, scenarios, and bottlenecks</p>
                  </div>
                  <div className="flex-1 overflow-hidden border rounded-lg">
                    <Copilot />
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>

          {/* Right Sidebar - Quick Stats (shown on larger screens) */}
          <div className="hidden xl:flex flex-col w-80 border-l p-4 overflow-y-auto">
            <h3 className="font-semibold mb-4">Quick Navigation</h3>
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push("/scenario")}
              >
                Build Scenario
              </Button>
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => router.push("/compare")}
              >
                Compare Results
              </Button>
            </div>
          </div>
        </div>

        {/* Patient Drawer */}
        {selectedPatientId && (
          <PatientDrawer
            patientId={selectedPatientId}
            onClose={() => setSelectedPatientId(null)}
          />
        )}

        {/* Command Palette */}
        <CommandPalette />
      </div>
    </TooltipProvider>
  );
}
