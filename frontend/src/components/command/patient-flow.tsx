"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
} from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Mock data for demo
const flowData = [
  { name: "ED", value: 120 },
  { name: "Admitted", value: 85 },
  { name: "Unit", value: 72 },
  { name: "ICU", value: 8 },
  { name: "Discharged", value: 65 },
];

const queueData = [
  { time: "00:00", edWait: 3, bedWait: 25, imaging: 2 },
  { time: "04:00", edWait: 2, bedWait: 20, imaging: 1 },
  { time: "08:00", edWait: 8, bedWait: 45, imaging: 4 },
  { time: "12:00", edWait: 12, bedWait: 60, imaging: 6 },
  { time: "16:00", edWait: 10, bedWait: 55, imaging: 5 },
  { time: "20:00", edWait: 6, bedWait: 35, imaging: 3 },
];

const occupancyData = [
  { time: "00:00", occupancy: 75 },
  { time: "04:00", occupancy: 70 },
  { time: "08:00", occupancy: 82 },
  { time: "12:00", occupancy: 92 },
  { time: "16:00", occupancy: 88 },
  { time: "20:00", occupancy: 78 },
];

export function PatientFlow() {
  return (
    <Tabs defaultValue="flow" className="h-full">
      <TabsList className="grid w-full grid-cols-3">
        <TabsTrigger value="flow">Patient Flow</TabsTrigger>
        <TabsTrigger value="queues">Queue Charts</TabsTrigger>
        <TabsTrigger value="occupancy">Occupancy</TabsTrigger>
      </TabsList>

      <TabsContent value="flow" className="h-[calc(100%-48px)]">
        <Card className="h-full">
          <CardHeader className="py-3">
            <CardTitle className="text-sm font-medium">
              Patient Flow (Today)
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100%-60px)]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={flowData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={80} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Bar
                  dataKey="value"
                  fill="hsl(var(--primary))"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="queues" className="h-[calc(100%-48px)]">
        <Card className="h-full">
          <CardHeader className="py-3">
            <CardTitle className="text-sm font-medium">
              Queue Lengths Over Time
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100%-60px)]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={queueData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="edWait"
                  name="ED Waiting"
                  stroke="#f97316"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="bedWait"
                  name="Bed Wait (min)"
                  stroke="#3b82f6"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="imaging"
                  name="Imaging Queue"
                  stroke="#a855f7"
                  strokeWidth={2}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="occupancy" className="h-[calc(100%-48px)]">
        <Card className="h-full">
          <CardHeader className="py-3">
            <CardTitle className="text-sm font-medium">
              Bed Occupancy Over Time
            </CardTitle>
          </CardHeader>
          <CardContent className="h-[calc(100%-60px)]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={occupancyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(var(--popover))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: "8px",
                  }}
                  formatter={(value: number) => [`${value}%`, "Occupancy"]}
                />
                <defs>
                  <linearGradient id="occupancyGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="occupancy"
                  stroke="#3b82f6"
                  fill="url(#occupancyGradient)"
                  strokeWidth={2}
                />
                {/* Warning threshold line */}
                <Line
                  type="monotone"
                  dataKey={() => 85}
                  stroke="#eab308"
                  strokeDasharray="5 5"
                  strokeWidth={1}
                  dot={false}
                  name="Warning"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
