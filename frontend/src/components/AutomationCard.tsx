import { Settings } from "lucide-react";
import { Handle, Position } from "reactflow";
import StatusBadge from "./StatusBadge";

export default function AutomationCard({ data }: { data: any }) {
  return (
    <div className="w-64 rounded-xl border border-white/15 bg-slate-900/80 p-4 shadow-glass backdrop-blur-xl">
      <Handle type="target" position={Position.Left} className="!bg-cyan-300" />
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[11px] uppercase tracking-[0.18em] text-cyan-200">{data.node_type}</p>
          <h3 className="mt-1 text-sm font-semibold text-white">{data.card_name}</h3>
        </div>
        <button className="rounded-lg border border-white/10 p-1.5 text-slate-300 hover:bg-white/10" onClick={() => data.onConfigure?.(data.id)}>
          <Settings size={15} />
        </button>
      </div>
      <p className="mt-3 line-clamp-2 min-h-10 text-xs leading-5 text-slate-300">{data.instruction_text || "No instruction configured."}</p>
      <div className="mt-4 flex items-center justify-between text-xs text-slate-400">
        <span>{data.screenshotCount || 0} screenshots</span>
        <span>{data.actionCount || 0} actions</span>
        <StatusBadge status={data.status || "draft"} />
      </div>
      <Handle type="source" position={Position.Right} className="!bg-cyan-300" />
    </div>
  );
}
