import React from "react";
import { Activity } from "lucide-react";

export function Header({ controllerStatus, mode }) {
  const getControllerColor = () => {
    if (controllerStatus === "ONLINE") return "text-green-500";
    if (controllerStatus === "UNKNOWN") return "text-orange-500";
    return "text-red-500";
  };

  const getModeColor = () => {
    if (mode === "AUTOMATIC") return "bg-blue-500";
    if (mode === "EMERGENCY") return "bg-red-500";
    if (mode === "DEGRADED") return "bg-orange-500";
    if (mode === "MANUAL") return "bg-purple-500";
    return "bg-gray-500";
  };

  return (
    <header className="mb-8 flex justify-between items-center bg-white p-4 rounded shadow">
      <h1 className="text-2xl font-bold text-gray-800">
        Factory Traffic Management
      </h1>
      <div className="flex gap-4">
        <span className="flex items-center gap-2 font-semibold">
          <Activity size={18} className={getControllerColor()} />
          {controllerStatus}
        </span>
        <span
          className={`px-3 py-1 rounded text-white font-bold ${getModeColor()}`}
        >
          {mode} MODE
        </span>
      </div>
    </header>
  );
}
