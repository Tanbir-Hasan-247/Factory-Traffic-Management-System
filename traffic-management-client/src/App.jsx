import React, { useEffect, useState } from "react";
import axios from "axios";
import { AlertTriangle } from "lucide-react";

import { Header } from "./components/Header";
import { JunctionVisual } from "./components/JunctionVisual";
import { SimulationControls } from "./components/SimulationControls";
import { HistoryList } from "./components/HistoryList";

// const API_BASE = "http://localhost:8000/api";
const API_BASE = "https://factory-traffic-management-system-phi.vercel.app/api";

function App() {
  const [junction, setJunction] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);

  const fetchJunction = async () => {
    try {
      const res = await axios.get(`${API_BASE}/junctions/A/status`);
      setJunction(res.data);
      setError(null);
    } catch (e) {
      console.error(e);
      setError("Cannot connect to backend or fetch junction.");
    }
  };

  const fetchHistory = async () => {
    try {
      const res = await axios.get(`${API_BASE}/junctions/A/history`);
      setHistory(res.data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchJunction();
    fetchHistory();
    const interval = setInterval(async () => {
      try {
        const res = await axios.get(`${API_BASE}/junctions/A/status`);
        setJunction(res.data);
        setError(null);
        if (
          res.data.controller_status === "ONLINE" &&
          res.data.pending_command
        ) {
          const payload = {
            junction_id: "A",
            status: "ACK",
            command_id: res.data.pending_command.command_id,
          };
          await axios.post(`${API_BASE}/controller-events`, payload);
          fetchJunction();
        }
      } catch (e) {
        console.error(e);
        setError("Cannot connect to backend or fetch junction.");
      }
      fetchHistory();
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const sequenceRef = React.useRef(Date.now());
  const nextSequence = () => {
    sequenceRef.current += 1;
    return sequenceRef.current;
  };

  const sendCommand = async (cmd) => {
    try {
      await axios.post(`${API_BASE}/junctions/A/commands`, cmd);
    } catch (e) {
      console.error(e);
      alert(
        e.response?.data?.detail ||
          e.response?.data?.error ||
          "Failed to send command",
      );
    }
  };

  const simulateVehicle = async (direction, type) => {
    try {
      await axios.post(`${API_BASE}/sensor-events`, {
        event_id: `evt-${crypto.randomUUID()}`,
        junction_id: "A",
        direction,
        event_type: "VEHICLE_ARRIVED",
        vehicle_id: `V-${crypto.randomUUID()}`,
        vehicle_type: type,
        sequence_no: nextSequence(),
        timestamp: new Date().toISOString(),
      });
    } catch (e) {
      console.error(e);
      alert(
        e.response?.data?.detail ||
          e.response?.data?.error ||
          "Failed to simulate vehicle",
      );
    }
  };
  const simulateClear = async (direction) => {
    try {
      await axios.post(`${API_BASE}/sensor-events`, {
        event_id: `evt-clr-${crypto.randomUUID()}`,
        junction_id: "A",
        direction,
        event_type: "VEHICLE_CLEARED",
        vehicle_id: "OLDEST",
        sequence_no: nextSequence(),
        timestamp: new Date().toISOString(),
      });
    } catch (e) {
      console.error(e);
      alert(
        e.response?.data?.detail ||
          e.response?.data?.error ||
          "No vehicle available to clear",
      );
    }
  };
  const simulateSensorFailure = async (direction, status) => {
    try {
      await axios.post(`${API_BASE}/sensor-events`, {
        event_id: `evt-snsr-${crypto.randomUUID()}`,
        junction_id: "A",
        direction,
        event_type: `SENSOR_${status}`,
        sequence_no: nextSequence(),
        timestamp: new Date().toISOString(),
      });
    } catch (e) {
      console.error(e);
      alert(
        e.response?.data?.detail ||
          e.response?.data?.error ||
          "Failed to simulate sensor",
      );
    }
  };

  if (error) {
    return (
      <div className="p-8 text-red-500 font-bold flex items-center gap-2">
        <AlertTriangle /> Error: {error}
      </div>
    );
  }

  if (!junction)
    return <div className="p-8">Loading or Backend Unavailable...</div>;

  return (
    <div className="min-h-screen p-8 bg-gray-100 font-sans">
      <Header
        controllerStatus={junction.controller_status}
        mode={junction.mode}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <JunctionVisual junction={junction} sendCommand={sendCommand} />

        <div className="flex flex-col gap-6">
          <SimulationControls
            simulateVehicle={simulateVehicle}
            simulateClear={simulateClear}
            simulateSensorFailure={simulateSensorFailure}
            pendingCommand={junction.pending_command}
            junction={junction}
          />
          <HistoryList history={history} />
        </div>
      </div>
    </div>
  );
}

export default App;
