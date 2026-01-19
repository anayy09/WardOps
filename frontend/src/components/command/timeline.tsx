"use client";

import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  Play,
  Pause,
  SkipForward,
  SkipBack,
  FastForward,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useCommandStore } from "@/stores/command-store";
import { formatTime } from "@/lib/utils";

export function Timeline() {
  const {
    currentTime,
    isPlaying,
    playbackSpeed,
    zoomLevel,
    setCurrentTime,
    setIsPlaying,
    setPlaybackSpeed,
    setZoomLevel,
    play,
    pause,
    stepForward,
    stepBackward,
  } = useCommandStore();

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Playback timer
  useEffect(() => {
    if (isPlaying) {
      intervalRef.current = setInterval(() => {
        setCurrentTime(new Date(currentTime.getTime() + 60000 * playbackSpeed));
      }, 1000);
    } else if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, playbackSpeed, currentTime, setCurrentTime]);

  // Calculate slider value (0-100 representing position in day)
  const startOfDay = new Date(currentTime);
  startOfDay.setHours(0, 0, 0, 0);
  const minutesSinceStart = (currentTime.getTime() - startOfDay.getTime()) / 60000;
  const sliderValue = (minutesSinceStart / 1440) * 100;

  const handleSliderChange = (value: number[]) => {
    const minutes = (value[0] / 100) * 1440;
    const newTime = new Date(startOfDay.getTime() + minutes * 60000);
    setCurrentTime(newTime);
  };

  const speedOptions = [1, 2, 5, 10];

  return (
    <div className="space-y-4">
      {/* Time display and zoom controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="text-2xl font-bold tabular-nums">
            {formatTime(currentTime)}
          </div>
          <div className="text-sm text-muted-foreground">
            {currentTime.toLocaleDateString("en-US", {
              weekday: "short",
              month: "short",
              day: "numeric",
            })}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Zoom level selector */}
          <div className="flex rounded-md border">
            {(["6h", "12h", "24h"] as const).map((level) => (
              <Button
                key={level}
                variant={zoomLevel === level ? "secondary" : "ghost"}
                size="sm"
                className="px-3"
                onClick={() => setZoomLevel(level)}
              >
                {level}
              </Button>
            ))}
          </div>

          {/* Speed selector */}
          <div className="flex items-center space-x-1 rounded-md border px-2">
            <FastForward className="h-4 w-4 text-muted-foreground" />
            {speedOptions.map((speed) => (
              <Button
                key={speed}
                variant={playbackSpeed === speed ? "secondary" : "ghost"}
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => setPlaybackSpeed(speed)}
              >
                {speed}x
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Timeline slider */}
      <div className="relative">
        {/* Time markers */}
        <div className="absolute -top-5 left-0 right-0 flex justify-between text-xs text-muted-foreground">
          {[0, 4, 8, 12, 16, 20, 24].map((hour) => (
            <span key={hour}>{hour.toString().padStart(2, "0")}:00</span>
          ))}
        </div>

        <Slider
          value={[sliderValue]}
          onValueChange={handleSliderChange}
          max={100}
          step={0.1}
          className="w-full"
        />

        {/* Event markers would go here */}
        <div className="absolute bottom-0 left-0 right-0 h-2">
          {/* Placeholder for event markers */}
        </div>
      </div>

      {/* Playback controls */}
      <div className="flex items-center justify-center space-x-2">
        <Button variant="outline" size="icon" onClick={stepBackward}>
          <SkipBack className="h-4 w-4" />
        </Button>

        <Button
          variant="default"
          size="icon"
          className="h-10 w-10"
          onClick={() => (isPlaying ? pause() : play())}
        >
          {isPlaying ? (
            <Pause className="h-5 w-5" />
          ) : (
            <Play className="h-5 w-5 ml-0.5" />
          )}
        </Button>

        <Button variant="outline" size="icon" onClick={stepForward}>
          <SkipForward className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
