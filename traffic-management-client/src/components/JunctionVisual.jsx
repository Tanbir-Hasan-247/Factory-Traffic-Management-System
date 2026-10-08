import React from "react";
import { AlertTriangle } from "lucide-react";
import { SignalLight } from "./SignalLight";

export function JunctionVisual({ junction, sendCommand }) {
  const isMismatch = ["NORTH", "SOUTH", "EAST", "WEST"].some(
    (dir) => junction.desired_signals?.[dir] !== junction.actual_signals?.[dir],
  );
  const isWaitingForAck = !!junction.pending_command;

  return (
    <div className="col-span-2 bg-white p-6 rounded shadow flex flex-col items-center">
      <div className="w-full flex justify-between items-center mb-8">
        <h2 className="text-xl font-semibold">
          Junction A - {junction.phase} Phase
        </h2>
        <div className="flex flex-col gap-2 items-end">
          {isWaitingForAck && (
            <span className="bg-orange-100 text-orange-700 px-3 py-1 rounded text-sm font-bold border border-orange-200 animate-pulse flex items-center gap-1">
              <AlertTriangle size={16} /> Waiting for Controller ACK...
            </span>
          )}
          {!isWaitingForAck &&
            isMismatch &&
            junction.controller_status !== "UNKNOWN" &&
            junction.controller_status !== "OFFLINE" && (
              <span className="bg-yellow-100 text-yellow-700 px-3 py-1 rounded text-sm font-bold border border-yellow-200 flex items-center gap-1">
                <AlertTriangle size={16} /> Signals Out of Sync
              </span>
            )}
          {junction.sensor_status &&
            Object.entries(junction.sensor_status).map(([dir, status]) =>
              status === "OFFLINE" ? (
                <span
                  key={dir}
                  className="bg-red-100 text-red-700 px-3 py-1 rounded text-sm font-bold border border-red-200 animate-pulse flex items-center gap-1"
                >
                  <AlertTriangle size={16} /> {dir} SENSOR OFFLINE
                </span>
              ) : null,
            )}
        </div>
      </div>
      <div className="relative w-96 h-96 bg-gray-700 border-4 border-gray-400 rounded-lg flex items-center justify-center">
        {}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 font-bold text-white bg-gray-800 px-2 py-1 rounded">
          NORTH (Q: {junction.queues.NORTH})
        </div>
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 font-bold text-white bg-gray-800 px-2 py-1 rounded">
          SOUTH (Q: {junction.queues.SOUTH})
        </div>
        <div className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 font-bold text-white bg-gray-800 px-2 py-1 rounded origin-center">
          WEST (Q: {junction.queues.WEST})
        </div>
        <div className="absolute right-2 top-1/2 -translate-y-1/2 rotate-90 font-bold text-white bg-gray-800 px-2 py-1 rounded origin-center">
          EAST (Q: {junction.queues.EAST})
        </div>

        {}

        {}
        <div className="absolute bottom-[55%] left-[58%] scale-75 origin-bottom-left">
          <SignalLight state={junction.actual_signals.NORTH} />
        </div>

        {}
        <div className="absolute top-[55%] right-[58%] scale-75 origin-top-right">
          <SignalLight state={junction.actual_signals.SOUTH} />
        </div>

        {}
        <div className="absolute top-[58%] left-[55%] scale-75 origin-top-left">
          <SignalLight state={junction.actual_signals.EAST} horizontal />
        </div>

        {}
        <div className="absolute bottom-[58%] right-[55%] scale-75 origin-bottom-right">
          <SignalLight state={junction.actual_signals.WEST} horizontal />
        </div>

        {}
        <div className="w-full h-8 bg-gray-500 absolute top-1/2 -translate-y-1/2 border-y-2 border-dashed border-gray-300" />
        <div className="h-full w-8 bg-gray-500 absolute left-1/2 -translate-x-1/2 border-x-2 border-dashed border-gray-300" />

        {}
        <div className="absolute bottom-[55%] left-1/2 -translate-x-1/2 flex flex-col-reverse gap-1 items-center z-10">
          {Array.from({ length: Math.min(junction.queues.NORTH, 5) }).map(
            (_, i) => (
              <div key={`n-${i}`} className="text-xl rotate-180 drop-shadow-md">
                🚘
              </div>
            ),
          )}
        </div>

        {}
        <div className="absolute top-[55%] left-1/2 -translate-x-1/2 flex flex-col gap-1 items-center z-10">
          {Array.from({ length: Math.min(junction.queues.SOUTH, 5) }).map(
            (_, i) => (
              <div key={`s-${i}`} className="text-xl drop-shadow-md">
                🚘
              </div>
            ),
          )}
        </div>

        {}
        <div className="absolute right-[55%] top-1/2 -translate-y-1/2 flex flex-row-reverse gap-1 items-center z-10">
          {Array.from({ length: Math.min(junction.queues.WEST, 5) }).map(
            (_, i) => (
              <div key={`w-${i}`} className="text-xl rotate-90 drop-shadow-md">
                🚘
              </div>
            ),
          )}
        </div>

        {}
        <div className="absolute left-[55%] top-1/2 -translate-y-1/2 flex flex-row gap-1 items-center z-10">
          {Array.from({ length: Math.min(junction.queues.EAST, 5) }).map(
            (_, i) => (
              <div key={`e-${i}`} className="text-xl -rotate-90 drop-shadow-md">
                🚘
              </div>
            ),
          )}
        </div>
      </div>

      <div className="mt-8 flex flex-col gap-2 w-full max-w-xs">
        <h3 className="font-bold text-gray-700 mb-2">Manual Control</h3>
        <button
          onClick={() =>
            sendCommand({ command: "MANUAL_GREEN_REQUEST", direction: "NORTH" })
          }
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 font-bold transition w-full text-left"
        >
          [ North/South Green ]
        </button>
        <button
          onClick={() =>
            sendCommand({ command: "MANUAL_GREEN_REQUEST", direction: "EAST" })
          }
          className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700 font-bold transition w-full text-left"
        >
          [ East/West Green ]
        </button>
        <button
          onClick={() => sendCommand({ command: "RETURN_TO_AUTOMATIC" })}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 font-bold transition w-full text-left"
        >
          [ Return To Automatic ]
        </button>
      </div>
    </div>
  );
}
