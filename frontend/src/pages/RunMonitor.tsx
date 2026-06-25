import { useEffect, useMemo, useState } from "react";
import { Check, RotateCcw, ShieldAlert, SkipForward, Square, X } from "lucide-react";
import { approveNodeRun, getRunActions, getRunEvents, getRunNodes, rejectNodeRun, skipNodeRun, stopRun } from "../api/client";

const base = import.meta.env.VITE_API_URL || "http://localhost:8000";

export default function RunMonitor() {
  const [runId, setRunId] = useState("");
  const [nodes, setNodes] = useState<any[]>([]);
  const [actions, setActions] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  async function load() {
    if (!runId) return;
    setNodes(await getRunNodes(Number(runId)));
    setActions(await getRunActions(Number(runId)));
    setEvents(await getRunEvents(Number(runId)));
  }
  useEffect(() => { const id = setInterval(load, 1500); return () => clearInterval(id); });
  const pending = useMemo(() => nodes.find((n) => n.status === "approval_required"), [nodes]);
  const latestShot = [...actions].reverse().find((a) => a.screenshot_path || a.before_screenshot_path || a.after_screenshot_path);
  const shot = latestShot?.after_screenshot_path || latestShot?.screenshot_path || latestShot?.before_screenshot_path;
  return <div className="space-y-5">
    <div className="flex flex-wrap gap-3"><input className="rounded-lg border border-white/10 bg-slate-900 px-3 py-2" placeholder="Run ID" value={runId} onChange={(e) => setRunId(e.target.value)} /><button className="rounded-lg bg-cyan-300 px-4 text-slate-950" onClick={load}>Load</button><button className="flex items-center gap-2 rounded-lg border border-red-300/30 px-4 text-red-200" onClick={() => runId && stopRun(Number(runId))}><Square size={16} /> Emergency stop</button></div>
    {pending && <section className="rounded-xl border border-amber-300/30 bg-amber-300/10 p-5"><div className="flex items-center gap-3"><ShieldAlert className="text-amber-200" /><div><h2 className="font-semibold text-amber-100">Approval Required</h2><p className="text-sm text-amber-50/80">Review the active card, screenshot, and safety notes before continuing.</p></div></div><div className="mt-4 flex gap-3"><button className="flex items-center gap-2 rounded-lg bg-emerald-300 px-4 py-2 text-slate-950" onClick={() => approveNodeRun(pending.id)}><Check size={16} />Approve once</button><button className="flex items-center gap-2 rounded-lg border border-red-300/40 px-4 py-2 text-red-200" onClick={() => rejectNodeRun(pending.id)}><X size={16} />Reject</button><button className="rounded-lg border border-slate-300/30 px-4 py-2 text-slate-200" onClick={() => runId && stopRun(Number(runId))}>Stop workflow</button></div></section>}
    <section className="grid gap-3 md:grid-cols-3">{nodes.map((n) => <div key={n.id} className={`rounded-lg border p-4 ${n.status === "completed" ? "border-emerald-300/30 bg-emerald-400/10" : n.status === "failed" ? "border-red-300/30 bg-red-400/10" : n.status === "approval_required" ? "border-amber-300/40 bg-amber-300/10 animate-pulse" : n.status === "stopped" ? "border-slate-300/30 bg-slate-400/10" : "border-cyan-300/30 bg-cyan-400/10"}`}><p className="font-semibold">Node {n.node_id}</p><p className="text-sm text-slate-300">{n.status}</p><div className="mt-3 flex gap-3 text-sm"><button className="flex items-center gap-1 text-cyan-200"><RotateCcw size={14} /> Retry</button><button className="flex items-center gap-1 text-amber-200" onClick={() => skipNodeRun(n.id)}><SkipForward size={14} /> Skip</button></div></div>)}</section>
    <section className="grid gap-5 lg:grid-cols-[1fr_360px]"><div className="rounded-xl border border-white/10 bg-slate-950/60 p-5"><h2 className="font-semibold">Action Status</h2><div className="mt-3 space-y-2 text-sm">{actions.map((a) => <div key={a.id} className="rounded-lg bg-white/5 p-3"><p><span className="text-cyan-200">{a.action_type}</span> {a.status}</p><p className="text-slate-400">confidence {a.confidence ?? "n/a"} coords {a.coordinates_json ? JSON.stringify(a.coordinates_json) : "n/a"}</p></div>)}</div></div><div className="rounded-xl border border-white/10 bg-slate-950/60 p-5"><h2 className="font-semibold">Screenshot Preview</h2>{shot ? <img className="mt-3 max-h-80 rounded-lg border border-white/10 object-contain" src={`${base}/api/screenshots/file?path=${encodeURIComponent(shot)}`} /> : <p className="mt-3 text-sm text-slate-400">No captured screenshot yet.</p>}</div></section>
    <section className="rounded-xl border border-white/10 bg-slate-950/60 p-5"><h2 className="font-semibold">Live Logs</h2><div className="mt-3 max-h-80 overflow-auto text-sm text-slate-300">{events.map((e) => <p key={e.id}><span className="text-cyan-200">{e.event_type}</span>: {e.message}</p>)}</div></section>
  </div>;
}
