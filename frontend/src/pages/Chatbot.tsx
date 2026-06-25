import { useEffect, useMemo, useState } from "react";
import { Bot, CheckCircle2, Circle, Download, Send, XCircle } from "lucide-react";
import { getWorkflows, runChat } from "../api/client";
import type { Workflow } from "../types";

interface EventItem { id: number; node_id?: number; event_type: string; message: string; payload?: any; created_at: string }

function ThinkingPanel({ events, workflowName }: { events: EventItem[]; workflowName?: string }) {
  const completed = events.filter((e) => e.event_type === "node_completed").length;
  const started = events.filter((e) => e.event_type === "node_started");
  const failed = events.find((e) => e.event_type.includes("failed"));
  const current = [...started].reverse().find((e) => !events.find((x) => x.event_type === "node_completed" && x.node_id === e.node_id));
  const progress = Math.min(100, completed * 10);
  return (
    <section className="rounded-xl border border-cyan-300/20 bg-slate-950/70 p-5 shadow-2xl shadow-cyan-950/30">
      <div className="flex items-center gap-3">
        <Bot className="text-cyan-200" />
        <div>
          <p className="text-sm text-cyan-100">Boss Agent is thinking...</p>
          <h2 className="text-lg font-semibold">Selected Workflow: {workflowName || "Waiting"}</h2>
        </div>
      </div>
      <div className="mt-5 h-2 overflow-hidden rounded-full bg-white/10">
        <div className="h-full bg-cyan-300 transition-all duration-500" style={{ width: `${progress}%` }} />
      </div>
      <div className="mt-5 space-y-2">
        {started.map((event) => {
          const done = events.some((e) => e.event_type === "node_completed" && e.node_id === event.node_id);
          const isCurrent = current?.node_id === event.node_id;
          return (
            <div key={`${event.id}-${event.node_id}`} className={`flex items-center gap-3 rounded-lg border px-3 py-2 ${done ? "border-emerald-300/30 bg-emerald-400/10" : isCurrent ? "border-cyan-200/50 bg-cyan-300/10 shadow-lg shadow-cyan-500/20 animate-pulse" : "border-white/10 bg-white/5"}`}>
              {done ? <CheckCircle2 size={18} className="text-emerald-300" /> : failed?.node_id === event.node_id ? <XCircle size={18} className="text-red-300" /> : <Circle size={18} className="text-slate-400" />}
              <span className="text-sm">{event.payload?.card_name || event.message.replace(" started", "")}</span>
            </div>
          );
        })}
      </div>
      <div className="mt-5 max-h-48 space-y-2 overflow-auto border-t border-white/10 pt-4 text-sm text-slate-300">
        {events.map((event) => <p key={event.id}><span className="text-cyan-200">{event.event_type}</span> {event.message}</p>)}
      </div>
    </section>
  );
}

export default function Chatbot() {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [workflowId, setWorkflowId] = useState<number | "">("");
  const [message, setMessage] = useState("sale nikal customer Acme Traders June 2021 se current date tak");
  const [events, setEvents] = useState<EventItem[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string>();
  const [finalAnswer, setFinalAnswer] = useState<any>();
  useEffect(() => { getWorkflows().then(setWorkflows); }, []);
  const reports = useMemo(() => finalAnswer?.reports || finalAnswer?.download_links || [], [finalAnswer]);
  async function send() {
    setEvents([]); setFinalAnswer(undefined);
    const res = await runChat({ user_message: message, workflow_id: workflowId || undefined, variables: {} });
    setSelectedWorkflow(res.selected_workflow.name);
    const source = new EventSource(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/workflow-runs/${res.run_id}/stream`);
    source.onmessage = (event) => setEvents((old) => [...old, JSON.parse(event.data)]);
    ["workflow_run_started", "node_started", "node_completed", "action_started", "action_completed", "workflow_completed", "workflow_failed", "action_failed", "node_failed"].forEach((name) => {
      source.addEventListener(name, (event: MessageEvent) => {
        const data = JSON.parse(event.data);
        setEvents((old) => [...old, data]);
        if (name === "workflow_completed") setFinalAnswer(data.payload?.final_output);
      });
    });
    source.addEventListener("close", () => source.close());
  }
  return (
    <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
      <section className="rounded-xl border border-white/10 bg-slate-950/60 p-5">
        <h1 className="text-2xl font-semibold">Chatbot</h1>
        <select className="mt-5 w-full rounded-lg border border-white/10 bg-slate-900 p-3" value={workflowId} onChange={(e) => setWorkflowId(e.target.value ? Number(e.target.value) : "")}>
          <option value="">Auto select workflow</option>
          {workflows.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
        </select>
        <textarea className="mt-4 h-36 w-full rounded-lg border border-white/10 bg-slate-900 p-3 text-sm" value={message} onChange={(e) => setMessage(e.target.value)} />
        <button onClick={send} className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-cyan-300 px-4 py-3 font-semibold text-slate-950"><Send size={18} /> Send</button>
        {finalAnswer?.answer && <div className="mt-5 rounded-lg border border-emerald-300/30 bg-emerald-400/10 p-4"><p>{finalAnswer.answer}</p></div>}
        <div className="mt-4 space-y-2">
          {Array.isArray(reports) && reports.map((r: any, i: number) => <a key={i} className="flex items-center gap-2 text-cyan-200" href={`${import.meta.env.VITE_API_URL || "http://localhost:8000"}${r.download_url || r}`}><Download size={16} /> {r.report_type || "Report"}</a>)}
        </div>
      </section>
      <ThinkingPanel events={events} workflowName={selectedWorkflow} />
    </div>
  );
}
