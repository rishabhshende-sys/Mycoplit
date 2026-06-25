import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AuditLog, Workflow } from "../types";

interface Stats {
  total_workflows: number;
  total_cards: number;
  uploaded_screenshots: number;
  recent_workflows: Workflow[];
  recent_audit_logs: AuditLog[];
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>();
  useEffect(() => { api.get("/api/dashboard").then((res) => setStats(res.data)); }, []);
  return (
    <div className="space-y-6">
      <header><h2 className="text-2xl font-semibold">Dashboard</h2><p className="text-sm text-slate-300">Read-only Phase 1 builder foundation.</p></header>
      <section className="grid grid-cols-3 gap-4">
        {[
          ["Total workflows", stats?.total_workflows ?? 0],
          ["Total cards", stats?.total_cards ?? 0],
          ["Uploaded screenshots", stats?.uploaded_screenshots ?? 0],
        ].map(([label, value]) => (
          <div key={label} className="rounded-xl border border-white/10 bg-panel p-5 shadow-glass backdrop-blur-xl">
            <p className="text-sm text-slate-400">{label}</p>
            <p className="mt-2 text-3xl font-semibold">{value}</p>
          </div>
        ))}
      </section>
      <section className="grid grid-cols-2 gap-4">
        <div className="panel"><h3 className="mb-3 font-semibold">Recent workflows</h3>{stats?.recent_workflows.map((workflow) => <p key={workflow.id} className="row">{workflow.name}</p>)}</div>
        <div className="panel"><h3 className="mb-3 font-semibold">Recent audit logs</h3>{stats?.recent_audit_logs.map((log) => <p key={log.id} className="row">{log.action} {log.entity_type}: {log.details}</p>)}</div>
      </section>
    </div>
  );
}
