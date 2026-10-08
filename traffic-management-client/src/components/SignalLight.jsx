import React from "react";

export function SignalLight({ state, horizontal = false }) {
  return (
    <div
      className={`flex ${horizontal ? "flex-row" : "flex-col"} bg-black p-2 rounded-lg gap-2 border-2 border-gray-600 relative`}
    >
      <div
        className={`w-6 h-6 rounded-full transition-all duration-300 ${state === "RED" ? "bg-red-500 shadow-[0_0_15px_red]" : "bg-red-900 opacity-30"}`}
      />
      <div
        className={`w-6 h-6 rounded-full transition-all duration-300 ${state === "YELLOW" ? "bg-yellow-400 shadow-[0_0_15px_yellow]" : "bg-yellow-900 opacity-30"}`}
      />
      <div
        className={`w-6 h-6 rounded-full transition-all duration-300 ${state === "GREEN" ? "bg-green-500 shadow-[0_0_15px_green]" : "bg-green-900 opacity-30"}`}
      />
      {state === "UNKNOWN" && (
        <span className="absolute inset-0 flex items-center justify-center text-xs text-white font-bold opacity-50">
          ?
        </span>
      )}
    </div>
  );
}
