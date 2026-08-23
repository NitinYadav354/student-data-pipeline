"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

type ConnectionState = "checking" | "connected" | "unreachable";

export default function Home() {
  const [state, setState] = useState<ConnectionState>("checking");

  useEffect(() => {
    let cancelled = false;

    fetch(`${API_BASE_URL}/health`)
      .then((res) => {
        if (!res.ok) throw new Error("bad response");
        return res.json();
      })
      .then(() => {
        if (!cancelled) setState("connected");
      })
      .catch(() => {
        if (!cancelled) setState("unreachable");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-zinc-50 font-sans">
      <h1 className="text-xl font-semibold text-zinc-900">
        Student Data Pipeline
      </h1>
      <p className="text-sm text-zinc-500">
        Setup checkpoint — the real UI lands in the next phase.
      </p>
      <StatusBadge state={state} />
      <p className="text-xs text-zinc-400">
        checking {API_BASE_URL}/health
      </p>
    </div>
  );
}

function StatusBadge({ state }: { state: ConnectionState }) {
  const copy = {
    checking: "Checking backend…",
    connected: "Backend connected",
    unreachable: "Backend unreachable — is uvicorn running on :8000?",
  }[state];

  const color = {
    checking: "bg-zinc-200 text-zinc-700",
    connected: "bg-emerald-100 text-emerald-700",
    unreachable: "bg-red-100 text-red-700",
  }[state];

  return (
    <span className={`rounded-full px-3 py-1 text-sm font-medium ${color}`}>
      {copy}
    </span>
  );
}
