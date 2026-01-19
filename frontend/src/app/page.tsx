"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import {
  Activity,
  BarChart3,
  Bed,
  Bot,
  Clock,
  Cpu,
  PlayCircle,
  Users,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useLoadDemo, useDemoStatus } from "@/hooks/use-api";

export default function HomePage() {
  const router = useRouter();
  const { data: status, isLoading: statusLoading } = useDemoStatus();
  const loadDemo = useLoadDemo();
  const [isLoading, setIsLoading] = useState(false);

  const handleLoadDemo = async () => {
    setIsLoading(true);
    try {
      await loadDemo.mutateAsync({ seed: 42 });
      router.push("/command");
    } catch (error) {
      console.error("Failed to load demo:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoToCommand = () => {
    router.push("/command");
  };

  const features = [
    {
      icon: Bed,
      title: "Floor Map",
      description: "Real-time bed status and occupancy visualization",
    },
    {
      icon: Clock,
      title: "Timeline Replay",
      description: "Scrub through historical data with event markers",
    },
    {
      icon: BarChart3,
      title: "Dashboards",
      description: "Patient flow, queues, and KPI metrics",
    },
    {
      icon: Cpu,
      title: "Simulation",
      description: "What-if scenario planning and comparison",
    },
    {
      icon: Bot,
      title: "AI Copilot",
      description: "LLM-powered operational insights with tool calling",
    },
    {
      icon: Zap,
      title: "Real-time",
      description: "WebSocket-based live updates",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] bg-center [mask-image:linear-gradient(180deg,white,rgba(255,255,255,0))]" />
        
        <div className="relative mx-auto max-w-7xl px-6 py-24 sm:py-32 lg:px-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="text-center"
          >
            {/* Logo */}
            <div className="mb-8 flex justify-center">
              <div className="flex items-center space-x-3">
                <div className="rounded-xl bg-blue-600 p-3">
                  <Activity className="h-10 w-10 text-white" />
                </div>
                <span className="text-4xl font-bold text-white">WardOps</span>
              </div>
            </div>

            {/* Headline */}
            <h1 className="text-4xl font-bold tracking-tight text-white sm:text-6xl">
              Hospital Operations
              <span className="block text-blue-400">Digital Twin</span>
            </h1>
            
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-slate-300">
              SimCity for hospital ops. Replay patient flow, simulate scenarios,
              and optimize operations with an AI-powered command center.
            </p>

            {/* CTA Buttons */}
            <div className="mt-10 flex items-center justify-center gap-4">
              {status?.data?.is_loaded ? (
                <Button
                  size="lg"
                  onClick={handleGoToCommand}
                  className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6"
                >
                  <PlayCircle className="mr-2 h-5 w-5" />
                  Go to Command Center
                </Button>
              ) : (
                <Button
                  size="lg"
                  onClick={handleLoadDemo}
                  disabled={isLoading || loadDemo.isPending}
                  className="bg-blue-600 hover:bg-blue-700 text-lg px-8 py-6"
                >
                  {isLoading || loadDemo.isPending ? (
                    <>
                      <Cpu className="mr-2 h-5 w-5 animate-spin" />
                      Loading Demo Data...
                    </>
                  ) : (
                    <>
                      <Zap className="mr-2 h-5 w-5" />
                      Load Demo Dataset
                    </>
                  )}
                </Button>
              )}
            </div>

            {/* Status Badge */}
            {status?.data?.is_loaded && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-6"
              >
                <span className="inline-flex items-center rounded-full bg-green-500/10 px-4 py-2 text-sm font-medium text-green-400 ring-1 ring-inset ring-green-500/20">
                  <span className="mr-2 h-2 w-2 rounded-full bg-green-400 animate-pulse" />
                  Demo data loaded: {status.data.patient_count} patients, {status.data.event_count} events
                </span>
              </motion.div>
            )}
          </motion.div>
        </div>
      </div>

      {/* Features Section */}
      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
        >
          <h2 className="text-center text-2xl font-semibold text-white mb-12">
            Command Center Features
          </h2>
          
          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.1 * index }}
              >
                <Card className="bg-slate-800/50 border-slate-700 hover:bg-slate-800/80 transition-colors">
                  <CardHeader>
                    <div className="mb-2 flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600/10">
                      <feature.icon className="h-6 w-6 text-blue-400" />
                    </div>
                    <CardTitle className="text-white">{feature.title}</CardTitle>
                    <CardDescription className="text-slate-400">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Tech Stack */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.5 }}
          className="mt-16 text-center"
        >
          <p className="text-sm text-slate-500">
            Built with Next.js • FastAPI • PostgreSQL • Redis • OpenAI
          </p>
        </motion.div>
      </div>
    </div>
  );
}
