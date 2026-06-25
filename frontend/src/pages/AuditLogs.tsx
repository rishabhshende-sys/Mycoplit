import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AuditLog } from "../types";

export default function AuditLogs() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  useEffect(() => { api.get("/api/audit-logs").then((res) => setLogs(res.data)); }, []);
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Audit Logs</h2>
      <div className="panel">
        {logs.map((log) => <div key={log.id} className="row">{new Date(log.created_at).toLocaleString()} - {log.action} - {log.entity_type} #{log.entity_id} - {log.details}</div>)}
      </div>
    </div>
  );
}
