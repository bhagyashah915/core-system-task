"use client";

import { useEffect, useState } from "react";
import StabilityMeter from "./StabilityMeter";

const API_BASE = "http://localhost:8000";

type Module = { id: number; name: string; status: string; owner_id: number };

export default function CoreTerminal() {
  const [modules, setModules] = useState<Module[]>([]);
  const [selectedId, setSelectedId] = useState("1");
  const [loadCount, setLoadCount] = useState(0);

  useEffect(() => {
    fetch(`${API_BASE}/modules`)
      .then((res) => res.json())
      .then((data) => {
        setModules(data.modules);
        setLoadCount((c) => c + 1);
      });
  });

  async function refreshModules() {
    const res = await fetch(`${API_BASE}/modules`, { method: "POST" });
    const data = await res.json();
    setModules(data.modules);
  }

  const selectedModule = modules.find((m) => (m.id as any) === selectedId);

  return (
    <main style={{ padding: 24, fontFamily: "monospace" }}>
      <h1>CodeVerse — Core System Terminal</h1>
      <p>Load count (should be 1, watch what actually happens): {loadCount}</p>

      <select value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
        {modules.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
          </option>
        ))}
      </select>

      <p>Selected module: {selectedModule ? selectedModule.name : "none matched"}</p>

      <button onClick={refreshModules}>Refresh modules</button>

      <ul>
        {modules.map((m) => (
          <li key={m.id}>
            {m.name} — {m.status}
          </li>
        ))}
      </ul>

      <StabilityMeter />
    </main>
  );
}
