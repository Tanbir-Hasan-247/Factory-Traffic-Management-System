import React from "react";
import { Clock } from "lucide-react";

export function HistoryList({ history }) {
  return (
    <div className="bg-white p-6 rounded shadow flex-1 overflow-auto max-h-[500px]">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Clock size={20} /> Recent History
      </h2>
      <div className="space-y-3">
        {history.map((h, i) => (
          <div key={h.id || i} className="text-sm border-b pb-2">
            <div className="font-semibold text-gray-700">{h.event_type}</div>
            <div className="text-gray-500 text-xs">
              {new Date(h.timestamp).toLocaleTimeString()}
            </div>
            <pre className="text-xs text-gray-500 mt-1 whitespace-pre-wrap">
              {JSON.stringify(h.details, null, 2)}
            </pre>
          </div>
        ))}
      </div>
    </div>
  );
}
