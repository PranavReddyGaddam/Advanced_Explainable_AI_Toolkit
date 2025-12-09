"use client";

/**
 * @author: @kokonutui
 * @description: AI Prompt Input for XAI Toolkit
 * @version: 1.0.0
 * @date: 2025-06-26
 * @license: MIT
 * @website: https://kokonutui.com
 * @github: https://github.com/kokonut-labs/kokonutui
 */

import { ArrowRight, Paperclip } from "lucide-react";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useAutoResizeTextarea } from "@/hooks/use-auto-resize-textarea";
import { cn } from "@/lib/utils";

interface AI_PromptProps {
  onSubmit: (text: string, selectedModel: string) => void;
  loading?: boolean;
  models?: Array<{ name: string; provider: string }>;
  selectedModel?: string;
  onModelChange?: (model: string) => void;
}

export default function AI_Prompt({ 
  onSubmit, 
  loading = false, 
  models = [],
  selectedModel = "",
  onModelChange = () => {}
}: AI_PromptProps) {
  const [value, setValue] = useState("");
  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 72,
    maxHeight: 300,
  });

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (value.trim() && !loading) {
      onSubmit(value.trim(), selectedModel);
      // setValue(""); // Removed to make prompt persist
      adjustHeight(true);
    }
  };

  return (
    <div className="w-4/6 py-4">
      <div className="relative">
        <div className="relative flex flex-col">
          <div className="overflow-y-auto" style={{ maxHeight: "400px" }}>
            <Textarea
              className={cn(
                "w-full resize-none rounded-xl rounded-b-none border border-white/30 bg-white/10 backdrop-blur-xl px-4 py-3 placeholder:text-white/60 text-white focus-visible:ring-2 focus-visible:ring-cyan-500 focus-visible:ring-offset-0 shadow-lg shadow-[0_0_20px_rgba(255,255,255,0.1)]",
                "min-h-[72px]"
              )}
              style={{ caretColor: 'white' }}
              id="ai-input-15"
              onChange={(e) => {
                setValue(e.target.value);
                adjustHeight();
              }}
              onKeyDown={handleKeyDown}
              placeholder={"Enter text to analyze with all XAI methods..."}
              ref={textareaRef}
              value={value}
              disabled={loading}
            />
          </div>

          <div className="flex h-14 items-center rounded-b-xl border border-white/30 bg-white/10 backdrop-blur-xl shadow-lg shadow-[0_0_20px_rgba(255,255,255,0.1)] border-t-0">
            <div className="absolute right-3 bottom-3 left-3 flex w-[calc(100%-24px)] items-center justify-between">
              <div className="flex items-center gap-2">
                <Select
                  value={selectedModel}
                  onValueChange={onModelChange}
                  disabled={loading}
                >
                  <SelectTrigger className="flex h-8 w-auto min-w-32 rounded-md border border-white/30 bg-white/20 backdrop-blur-md px-3 py-1 text-sm text-white focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:ring-offset-0 disabled:cursor-not-allowed disabled:opacity-50">
                    <SelectValue placeholder="Select model" />
                  </SelectTrigger>
                  <SelectContent className="bg-white/10 backdrop-blur-xl border border-white/30 text-white">
                    {models.map((model) => (
                      <SelectItem key={model.name} value={model.name} className="text-white hover:bg-white/20">
                        {model.name} ({model.provider})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="mx-0.5 h-4 w-px bg-white/30" />
                <label
                  aria-label="Attach file"
                  className={cn(
                    "cursor-pointer rounded-lg bg-white/20 backdrop-blur-md p-2",
                    "hover:bg-white/30 focus-visible:ring-1 focus-visible:ring-cyan-500 focus-visible:ring-offset-0",
                    "text-white/80 hover:text-white"
                  )}
                >
                  <input className="hidden" type="file" />
                  <Paperclip className="h-4 w-4 transition-colors" />
                </label>
              </div>
              <button
                aria-label="Send message"
                className={cn(
                  "rounded-lg bg-cyan-500/80 backdrop-blur-md p-2",
                  "hover:bg-cyan-500/90 focus-visible:ring-1 focus-visible:ring-cyan-500 focus-visible:ring-offset-0",
                  "text-white shadow-lg shadow-[0_0_15px_rgba(6,182,212,0.3)]",
                  value.trim() && !loading ? "opacity-100" : "opacity-50 cursor-not-allowed"
                )}
                disabled={!value.trim() || loading}
                onClick={handleSubmit}
                type="button"
              >
                <ArrowRight className="h-4 w-4 transition-opacity duration-200" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
