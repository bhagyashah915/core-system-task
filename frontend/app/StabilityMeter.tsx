"use client";

import { useEffect, useState } from "react";

const API_BASE = "http://localhost:8000";

export default function StabilityMeter() {
  const [ticks, setTicks] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setTicks((t) => t + 1);
      fetch(`${API_BASE}/core/status`);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  return <p>Core stability pings sent: {ticks}</p>;
}
