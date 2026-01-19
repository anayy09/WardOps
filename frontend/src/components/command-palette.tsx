"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Command,
  Search,
  Home,
  LayoutDashboard,
  FlaskConical,
  GitCompare,
  Play,
  Pause,
  Sun,
  Moon,
  Settings,
  User,
  FileText,
  BarChart2,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useCommandStore } from "@/stores/command-store";

interface CommandItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  shortcut?: string;
  action: () => void;
  category: string;
}

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const router = useRouter();
  const { theme, setTheme } = useTheme();
  const { isPlaying, setIsPlaying } = useCommandStore();

  const commands: CommandItem[] = [
    // Navigation
    {
      id: "nav-home",
      label: "Go to Home",
      icon: <Home className="h-4 w-4" />,
      shortcut: "G H",
      action: () => router.push("/"),
      category: "Navigation",
    },
    {
      id: "nav-command",
      label: "Go to Command Center",
      icon: <LayoutDashboard className="h-4 w-4" />,
      shortcut: "G C",
      action: () => router.push("/command"),
      category: "Navigation",
    },
    {
      id: "nav-scenario",
      label: "Go to Scenario Builder",
      icon: <FlaskConical className="h-4 w-4" />,
      shortcut: "G S",
      action: () => router.push("/scenario"),
      category: "Navigation",
    },
    {
      id: "nav-compare",
      label: "Go to Compare View",
      icon: <GitCompare className="h-4 w-4" />,
      shortcut: "G D",
      action: () => router.push("/compare"),
      category: "Navigation",
    },

    // Actions
    {
      id: "action-play",
      label: isPlaying ? "Pause Replay" : "Start Replay",
      icon: isPlaying ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />,
      shortcut: "Space",
      action: () => setIsPlaying(!isPlaying),
      category: "Actions",
    },
    {
      id: "action-theme",
      label: theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode",
      icon: theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />,
      shortcut: "T",
      action: () => setTheme(theme === "dark" ? "light" : "dark"),
      category: "Actions",
    },

    // Quick Views
    {
      id: "view-kpis",
      label: "View KPI Dashboard",
      icon: <BarChart2 className="h-4 w-4" />,
      action: () => {
        router.push("/command");
        // Could scroll to KPIs section
      },
      category: "Quick Views",
    },
    {
      id: "view-policies",
      label: "View Policy Documents",
      icon: <FileText className="h-4 w-4" />,
      action: () => {
        // Could open a policy viewer
      },
      category: "Quick Views",
    },
  ];

  const filteredCommands = commands.filter(
    (cmd) =>
      cmd.label.toLowerCase().includes(search.toLowerCase()) ||
      cmd.category.toLowerCase().includes(search.toLowerCase())
  );

  const groupedCommands = filteredCommands.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = [];
    acc[cmd.category].push(cmd);
    return acc;
  }, {} as Record<string, CommandItem[]>);

  // Keyboard handlers
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Open command palette with Cmd/Ctrl + K
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setOpen((prev) => !prev);
        setSearch("");
        setSelectedIndex(0);
      }

      // Close with Escape
      if (e.key === "Escape" && open) {
        setOpen(false);
      }

      // Navigate with arrows
      if (open) {
        if (e.key === "ArrowDown") {
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < filteredCommands.length - 1 ? prev + 1 : 0
          );
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : filteredCommands.length - 1
          );
        }
        if (e.key === "Enter" && filteredCommands[selectedIndex]) {
          e.preventDefault();
          filteredCommands[selectedIndex].action();
          setOpen(false);
        }
      }

      // Global shortcuts when palette is closed
      if (!open) {
        // Space for play/pause
        if (e.code === "Space" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
          e.preventDefault();
          setIsPlaying(!isPlaying);
        }
        // T for theme toggle
        if (e.key === "t" && !["INPUT", "TEXTAREA"].includes((e.target as HTMLElement).tagName)) {
          setTheme(theme === "dark" ? "light" : "dark");
        }
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [open, filteredCommands, selectedIndex, isPlaying, setIsPlaying, theme, setTheme, router]);

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/50"
            onClick={() => setOpen(false)}
          />

          {/* Command Palette */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="fixed left-1/2 top-[20%] z-50 w-full max-w-lg -translate-x-1/2 rounded-xl border bg-background shadow-2xl"
          >
            {/* Search Input */}
            <div className="flex items-center gap-2 border-b px-4 py-3">
              <Search className="h-5 w-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="Type a command or search..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setSelectedIndex(0);
                }}
                className="flex-1 bg-transparent text-sm outline-none placeholder:text-muted-foreground"
                autoFocus
              />
              <kbd className="rounded border bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                ESC
              </kbd>
            </div>

            {/* Command List */}
            <div className="max-h-[300px] overflow-y-auto p-2">
              {Object.entries(groupedCommands).map(([category, items]) => (
                <div key={category} className="mb-2">
                  <p className="mb-1 px-2 text-xs font-medium text-muted-foreground">
                    {category}
                  </p>
                  {items.map((cmd) => {
                    const globalIndex = filteredCommands.indexOf(cmd);
                    return (
                      <button
                        key={cmd.id}
                        onClick={() => {
                          cmd.action();
                          setOpen(false);
                        }}
                        className={`flex w-full items-center justify-between rounded-md px-2 py-2 text-sm transition-colors ${
                          globalIndex === selectedIndex
                            ? "bg-accent text-accent-foreground"
                            : "hover:bg-muted"
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          {cmd.icon}
                          <span>{cmd.label}</span>
                        </div>
                        {cmd.shortcut && (
                          <kbd className="text-xs text-muted-foreground">
                            {cmd.shortcut}
                          </kbd>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}

              {filteredCommands.length === 0 && (
                <p className="py-4 text-center text-sm text-muted-foreground">
                  No commands found.
                </p>
              )}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between border-t px-4 py-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-2">
                <Command className="h-3 w-3" />
                <span>WardOps Command Palette</span>
              </div>
              <div className="flex items-center gap-2">
                <kbd className="rounded border bg-muted px-1 py-0.5">↑↓</kbd>
                <span>Navigate</span>
                <kbd className="rounded border bg-muted px-1 py-0.5">↵</kbd>
                <span>Select</span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
