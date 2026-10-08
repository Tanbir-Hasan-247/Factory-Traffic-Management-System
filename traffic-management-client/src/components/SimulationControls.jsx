import React, { useState } from "react";
import { Settings, Server } from "lucide-react";
import axios from "axios";

const API_BASE = "https://factory-traffic-management-system-phi.vercel.app/api";

export function SimulationControls({
  simulateVehicle,
  simulateClear,
  simulateSensorFailure,
  pendingCommand,
  junction,
}) {
  const [direction, setDirection] = useState("NORTH");
  const [vehicleType, setVehicleType] = useState("TRUCK");

  const sendControllerEvent = async (status) => {
    try {
      const payload = { junction_id: "A", status };
      if (status === "ACK" && pendingCommand?.command_id) {
        payload.command_id = pendingCommand.command_id;
      } else if (status === "ACK") {
        alert("No pending command to ACK");
        return;
      } else if (status === "ONLINE") {
        payload.actual_signals = {
          NORTH: "RED",
          SOUTH: "RED",
          EAST: "RED",
          WEST: "RED",
        };
      }

      await axios.post(`${API_BASE}/controller-events`, payload);
    } catch (e) {
      console.error(e);
      alert("Failed to send controller event");
    }
  };

  const handleAutoClear = () => {
    if (!junction) return;
    const validDirections = Object.entries(junction.actual_signals)
      .filter(([dir, signal]) => signal === "GREEN" && junction.queues[dir] > 0)
      .map(([dir]) => dir);

    if (validDirections.length > 0) {
      simulateClear(validDirections[0]);
    } else {
      alert("No vehicles waiting in any GREEN direction.");
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Settings size={20} /> Vehicle Simulation
        </h2>

        <div className="flex flex-col gap-3 mb-4">
          <div className="flex justify-between items-center">
            <label className="font-semibold text-gray-700 text-sm">
              Direction:
            </label>
            <select
              className="border p-1 rounded text-sm w-40"
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
            >
              <option value="NORTH">NORTH</option>
              <option value="SOUTH">SOUTH</option>
              <option value="EAST">EAST</option>
              <option value="WEST">WEST</option>
            </select>
          </div>
          <div className="flex justify-between items-center">
            <label className="font-semibold text-gray-700 text-sm">
              Vehicle Type:
            </label>
            <select
              className="border p-1 rounded text-sm w-40"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
            >
              <option value="EMERGENCY">EMERGENCY</option>
              <option value="TRUCK">TRUCK</option>
              <option value="FORKLIFT">FORKLIFT</option>
              <option value="EMPLOYEE_VEHICLE">EMPLOYEE_VEHICLE</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2">
          <button
            onClick={() => simulateVehicle(direction, vehicleType)}
            className="px-2 py-2 bg-blue-100 text-blue-700 rounded text-sm font-bold border border-blue-200 hover:bg-blue-200 transition"
          >
            Vehicle Arrived
          </button>
          <button
            onClick={handleAutoClear}
            className="px-2 py-2 bg-green-100 text-green-700 rounded text-sm font-bold border border-green-200 hover:bg-green-200 transition"
          >
            Auto-Clear (Green Phase)
          </button>
        </div>

        <div className="grid grid-cols-2 gap-2 pt-2 mt-2 border-t">
          <button
            onClick={() => simulateSensorFailure(direction, "OFFLINE")}
            className="px-2 py-2 bg-orange-100 text-orange-700 rounded text-sm font-bold border border-orange-200 hover:bg-orange-200 transition"
          >
            Sensor Offline
          </button>
          <button
            onClick={() => simulateSensorFailure(direction, "ONLINE")}
            className="px-2 py-2 bg-gray-100 text-gray-700 rounded text-sm font-bold border border-gray-200 hover:bg-gray-200 transition"
          >
            Sensor Online
          </button>
        </div>
      </div>

      <div className="bg-white p-6 rounded shadow">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Server size={20} /> Controller Simulation
        </h2>
        <div className="flex flex-col gap-2">
          <button
            onClick={() => sendControllerEvent("OFFLINE")}
            className="px-2 py-2 bg-red-100 text-red-700 rounded text-sm font-bold border border-red-200 hover:bg-red-200 transition text-left pl-4"
          >
            [ Controller Offline ]
          </button>
          <button
            onClick={() => sendControllerEvent("ONLINE")}
            className="px-2 py-2 bg-green-100 text-green-700 rounded text-sm font-bold border border-green-200 hover:bg-green-200 transition text-left pl-4"
          >
            [ Controller Online ]
          </button>
          <button
            onClick={() => sendControllerEvent("ACK")}
            className="px-2 py-2 bg-gray-100 text-gray-700 rounded text-sm font-bold border border-gray-200 hover:bg-gray-200 transition text-left pl-4 disabled:opacity-50"
            disabled={!pendingCommand}
          >
            [ Send ACK{" "}
            {pendingCommand
              ? `(${pendingCommand.command_id.split("-")[1]})`
              : ""}{" "}
            ]
          </button>
        </div>
      </div>
    </div>
  );
}
