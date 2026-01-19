"use client";

import { motion } from "framer-motion";
import {
  Bed,
  Clock,
  AlertTriangle,
  Users,
  Activity,
  Timer,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface KPIMetrics {
  occupancy_percent: number;
  average_los_hours: number;
  average_time_to_bed_minutes: number;
  sla_breaches: number;
  imaging_queue_length: number;
  ed_waiting_count: number;
  nurse_load_average: number;
}

interface KPICardsProps {
  metrics: KPIMetrics | undefined;
  isLoading: boolean;
}

export function KPICards({ metrics, isLoading }: KPICardsProps) {
  const cards = [
    {
      title: "Occupancy",
      value: metrics?.occupancy_percent ?? 0,
      format: (v: number) => `${v.toFixed(1)}%`,
      icon: Bed,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      threshold: { warning: 85, critical: 95 },
    },
    {
      title: "Avg LOS",
      value: metrics?.average_los_hours ?? 0,
      format: (v: number) => `${v.toFixed(1)}h`,
      icon: Clock,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
    {
      title: "Time to Bed",
      value: metrics?.average_time_to_bed_minutes ?? 0,
      format: (v: number) => `${v.toFixed(0)}m`,
      icon: Timer,
      color: "text-amber-500",
      bgColor: "bg-amber-500/10",
      threshold: { warning: 45, critical: 60 },
    },
    {
      title: "SLA Breaches",
      value: metrics?.sla_breaches ?? 0,
      format: (v: number) => v.toString(),
      icon: AlertTriangle,
      color: "text-red-500",
      bgColor: "bg-red-500/10",
      threshold: { warning: 1, critical: 5 },
    },
    {
      title: "ED Waiting",
      value: metrics?.ed_waiting_count ?? 0,
      format: (v: number) => v.toString(),
      icon: Users,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
      threshold: { warning: 5, critical: 10 },
    },
    {
      title: "Nurse Load",
      value: metrics?.nurse_load_average ?? 0,
      format: (v: number) => `${v.toFixed(1)}:1`,
      icon: Activity,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      threshold: { warning: 4, critical: 5 },
    },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-6 gap-4">
        {Array(6)
          .fill(0)
          .map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardContent className="p-4">
                <div className="h-4 w-16 rounded bg-muted" />
                <div className="mt-2 h-8 w-12 rounded bg-muted" />
              </CardContent>
            </Card>
          ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-6 gap-4">
      {cards.map((card, index) => {
        const Icon = card.icon;
        let statusColor = "";
        
        if (card.threshold) {
          if (card.value >= card.threshold.critical) {
            statusColor = "border-red-500/50";
          } else if (card.value >= card.threshold.warning) {
            statusColor = "border-amber-500/50";
          }
        }

        return (
          <motion.div
            key={card.title}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card className={cn("transition-colors", statusColor)}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-muted-foreground">
                    {card.title}
                  </span>
                  <div className={cn("rounded-md p-1.5", card.bgColor)}>
                    <Icon className={cn("h-4 w-4", card.color)} />
                  </div>
                </div>
                <div className="mt-2">
                  <span className="text-2xl font-bold">
                    {card.format(card.value)}
                  </span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        );
      })}
    </div>
  );
}
