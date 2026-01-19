"use client";

import { motion } from "framer-motion";
import { cn, getStatusColor, getAcuityColor } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Bed {
  id: number;
  bed_number: string;
  bed_type: string;
  status: string;
  x_position: number;
  y_position: number;
  current_patient_id: number | null;
  patient_name?: string;
  patient_acuity?: string;
  patient_chief_complaint?: string;
}

interface FloorMapProps {
  beds: Bed[];
  isLoading: boolean;
  onBedClick: (bed: Bed) => void;
}

export function FloorMap({ beds, isLoading, onBedClick }: FloorMapProps) {
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  // Calculate bounds for scaling
  const minX = Math.min(...beds.map((b) => b.x_position)) - 50;
  const maxX = Math.max(...beds.map((b) => b.x_position)) + 100;
  const minY = Math.min(...beds.map((b) => b.y_position)) - 50;
  const maxY = Math.max(...beds.map((b) => b.y_position)) + 100;
  
  const viewBox = `${minX} ${minY} ${maxX - minX} ${maxY - minY}`;

  return (
    <div className="h-full w-full">
      <svg
        viewBox={viewBox}
        className="h-full w-full"
        preserveAspectRatio="xMidYMid meet"
      >
        {/* Background grid */}
        <defs>
          <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
            <path
              d="M 50 0 L 0 0 0 50"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-muted-foreground/20"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />

        {/* Nurse stations */}
        <rect
          x={130}
          y={250}
          width={80}
          height={40}
          rx={4}
          className="fill-muted stroke-muted-foreground/50"
        />
        <text
          x={170}
          y={275}
          textAnchor="middle"
          className="fill-muted-foreground text-[10px]"
        >
          Nurse Station
        </text>

        <rect
          x={330}
          y={250}
          width={80}
          height={40}
          rx={4}
          className="fill-muted stroke-muted-foreground/50"
        />
        <text
          x={370}
          y={275}
          textAnchor="middle"
          className="fill-muted-foreground text-[10px]"
        >
          Nurse Station
        </text>

        {/* Beds */}
        {beds.map((bed) => (
          <BedNode key={bed.id} bed={bed} onClick={() => onBedClick(bed)} />
        ))}

        {/* Legend */}
        <g transform={`translate(${minX + 10}, ${maxY - 80})`}>
          <text className="fill-muted-foreground text-[10px] font-medium">
            Status Legend
          </text>
          {["empty", "occupied", "cleaning", "blocked", "isolation"].map(
            (status, i) => (
              <g key={status} transform={`translate(0, ${15 + i * 14})`}>
                <circle
                  r={4}
                  cx={4}
                  cy={0}
                  className={cn(getStatusColor(status))}
                />
                <text
                  x={14}
                  y={4}
                  className="fill-muted-foreground text-[9px] capitalize"
                >
                  {status}
                </text>
              </g>
            )
          )}
        </g>
      </svg>
    </div>
  );
}

function BedNode({ bed, onClick }: { bed: Bed; onClick: () => void }) {
  const statusColors: Record<string, string> = {
    empty: "#22c55e",
    occupied: "#3b82f6",
    cleaning: "#eab308",
    blocked: "#ef4444",
    isolation: "#a855f7",
  };

  const acuityColors: Record<string, string> = {
    low: "#22c55e",
    medium: "#eab308",
    high: "#f97316",
    critical: "#ef4444",
  };

  const color = statusColors[bed.status] || "#6b7280";
  const isOccupied = bed.status === "occupied";
  const acuityColor = bed.patient_acuity
    ? acuityColors[bed.patient_acuity] || "#6b7280"
    : null;

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <motion.g
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.3 }}
          onClick={onClick}
          className="cursor-pointer"
        >
          {/* Bed rectangle */}
          <motion.rect
            x={bed.x_position}
            y={bed.y_position}
            width={60}
            height={40}
            rx={4}
            fill={color}
            fillOpacity={0.2}
            stroke={color}
            strokeWidth={2}
            whileHover={{ scale: 1.05 }}
            transition={{ type: "spring", stiffness: 400 }}
          />
          
          {/* Bed number */}
          <text
            x={bed.x_position + 30}
            y={bed.y_position + 15}
            textAnchor="middle"
            className="fill-foreground text-[10px] font-medium"
          >
            {bed.bed_number.split("-")[1]}
          </text>

          {/* Patient indicator */}
          {isOccupied && (
            <>
              <circle
                cx={bed.x_position + 30}
                cy={bed.y_position + 30}
                r={6}
                fill={acuityColor || color}
              />
              {bed.patient_acuity === "critical" && (
                <motion.circle
                  cx={bed.x_position + 30}
                  cy={bed.y_position + 30}
                  r={10}
                  fill="none"
                  stroke={acuityColor || "#ef4444"}
                  strokeWidth={1}
                  animate={{ scale: [1, 1.3, 1], opacity: [1, 0.5, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}
            </>
          )}

          {/* Isolation indicator */}
          {bed.bed_type === "isolation" && (
            <circle
              cx={bed.x_position + 55}
              cy={bed.y_position + 5}
              r={4}
              fill="#a855f7"
            />
          )}
        </motion.g>
      </TooltipTrigger>
      <TooltipContent side="right" className="max-w-xs">
        <div className="space-y-1">
          <p className="font-semibold">{bed.bed_number}</p>
          <p className="text-xs capitalize">Status: {bed.status}</p>
          <p className="text-xs">Type: {bed.bed_type}</p>
          {bed.patient_name && (
            <>
              <hr className="my-1" />
              <p className="text-xs font-medium">{bed.patient_name}</p>
              <p className={cn("text-xs capitalize", getAcuityColor(bed.patient_acuity || ""))}>
                Acuity: {bed.patient_acuity}
              </p>
              {bed.patient_chief_complaint && (
                <p className="text-xs text-muted-foreground">
                  {bed.patient_chief_complaint}
                </p>
              )}
            </>
          )}
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
