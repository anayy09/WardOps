"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Send,
  Loader2,
  AlertCircle,
  ChevronDown,
  Play,
  Eye,
  FileText,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { useCopilotChat, useCopilotStatus } from "@/hooks/use-api";
import { cn } from "@/lib/utils";

interface Message {
  role: "user" | "assistant";
  content: string;
  toolCalls?: any[];
  actions?: any[];
  citations?: any[];
}

export function Copilot() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const { data: status } = useCopilotStatus();
  const chatMutation = useCopilotChat();

  const isAvailable = status?.available ?? false;

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || chatMutation.isPending) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    try {
      const response = await chatMutation.mutateAsync({
        messages: [...messages, userMessage].map((m) => ({
          role: m.role,
          content: m.content,
        })),
      });

      const assistantMessage: Message = {
        role: "assistant",
        content: response.content,
        toolCalls: response.tool_calls,
        actions: response.actions,
        citations: response.citations,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestedPrompts = [
    "What's the current occupancy status?",
    "Summarize today's bottlenecks",
    "Show me high acuity patients",
    "Create a surge scenario",
  ];

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b p-4">
        <div className="flex items-center space-x-2">
          <Bot className="h-5 w-5 text-primary" />
          <h3 className="text-sm font-semibold">Ops Copilot</h3>
        </div>
        <Badge variant={isAvailable ? "success" : "secondary"} className="text-xs">
          {isAvailable ? "Online" : "Offline"}
        </Badge>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 p-4" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Bot className="mb-4 h-12 w-12 text-muted-foreground/50" />
            <p className="mb-4 text-sm text-muted-foreground">
              Ask me about unit operations, patient flow, or create scenarios.
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestedPrompts.map((prompt) => (
                <Button
                  key={prompt}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => setInput(prompt)}
                >
                  {prompt}
                </Button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className={cn(
                    "flex",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[85%] rounded-lg px-3 py-2 text-sm",
                      message.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "bg-muted"
                    )}
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>

                    {/* Tool calls */}
                    {message.toolCalls && message.toolCalls.length > 0 && (
                      <div className="mt-2 space-y-1 border-t border-border/50 pt-2">
                        {message.toolCalls.map((tc, i) => (
                          <div
                            key={i}
                            className="flex items-center space-x-1 text-xs text-muted-foreground"
                          >
                            <FileText className="h-3 w-3" />
                            <span>Called: {tc.name}</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Citations */}
                    {message.citations && message.citations.length > 0 && (
                      <div className="mt-2 space-y-1 border-t border-border/50 pt-2">
                        {message.citations.map((citation, i) => (
                          <Badge
                            key={i}
                            variant="outline"
                            className="text-xs"
                          >
                            📄 {citation.doc_title}
                          </Badge>
                        ))}
                      </div>
                    )}

                    {/* Actions */}
                    {message.actions && message.actions.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-2 border-t border-border/50 pt-2">
                        {message.actions.map((action, i) => (
                          <Button
                            key={i}
                            variant="secondary"
                            size="sm"
                            className="h-7 text-xs"
                          >
                            {action.type === "run_simulation" && (
                              <Play className="mr-1 h-3 w-3" />
                            )}
                            {action.type === "open_view" && (
                              <Eye className="mr-1 h-3 w-3" />
                            )}
                            {action.label}
                          </Button>
                        ))}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {chatMutation.isPending && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="flex items-center space-x-2 rounded-lg bg-muted px-3 py-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-sm text-muted-foreground">
                    Thinking...
                  </span>
                </div>
              </motion.div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <div className="border-t p-4">
        {!isAvailable && (
          <div className="mb-2 flex items-center space-x-2 rounded-md bg-amber-500/10 px-3 py-2 text-xs text-amber-500">
            <AlertCircle className="h-4 w-4" />
            <span>Copilot requires LLM_API_URL and LLM_API_KEY to be configured in backend</span>
          </div>
        )}
        <div className="flex space-x-2">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about operations..."
            disabled={!isAvailable || chatMutation.isPending}
            className="flex-1"
          />
          <Button
            onClick={handleSend}
            disabled={!input.trim() || !isAvailable || chatMutation.isPending}
            size="icon"
          >
            {chatMutation.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
