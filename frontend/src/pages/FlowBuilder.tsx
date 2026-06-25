import { Save, ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { getWorkflow, getWorkflows, updateWorkflow } from "../api/client";
import CardConfigPanel from "../components/CardConfigPanel";
import WorkflowCanvas from "../components/WorkflowCanvas";
import { useWorkflowStore } from "../store/workflowStore";
import type { Workflow } from "../types";

export default function FlowBuilder({ activeWorkflowId }: { activeWorkflowId?: number }) {
  const [workflow, setWorkflow] = useState<Workflow>();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const { selectedNodeId, setSelectedNodeId, setActiveWorkflowId } = useWorkflowStore();
  const load = useCallback((id?: number) => {
    getWorkflows().then((items) => {
      setWorkflows(items);
      const nextId = id || activeWorkflowId || items[0]?.id;
      if (nextId) {
        setActiveWorkflowId(nextId);
        getWorkflow(nextId).then(setWorkflow);
      }
    });
  }, [activeWorkflowId, setActiveWorkflowId]);
  useEffect(() => load(), [load]);
  const selectedNode = useMemo(() => workflow?.nodes.find((node) => node.id === selectedNodeId), [workflow, selectedNodeId]);

  async function savePatch(patch: Partial<Workflow>) {
    if (!workflow) return;
    const saved = await updateWorkflow(workflow.id, patch);
    setWorkflow(saved);
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <select className="field max-w-xs" value={workflow?.id || ""} onChange={(event) => load(Number(event.target.value))}>
          {workflows.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
        <input className="field max-w-md" value={workflow?.name || ""} onChange={(event) => workflow && setWorkflow({ ...workflow, name: event.target.value })} />
        <button className="btn flex items-center gap-2" onClick={() => workflow && savePatch({ name: workflow.name })}><Save size={16} />Save workflow</button>
        <label className="flex items-center gap-2 rounded-lg border border-amber-300/20 bg-amber-300/10 px-3 py-2 text-sm text-amber-100"><input type="checkbox" checked={!!workflow?.gui_actions_enabled} onChange={(e) => savePatch({ gui_actions_enabled: e.target.checked })} />Enable GUI actions</label>
        <label className="flex items-center gap-2 rounded-lg border border-cyan-300/20 bg-cyan-300/10 px-3 py-2 text-sm text-cyan-100"><input type="checkbox" checked={workflow?.approval_required ?? true} onChange={(e) => savePatch({ approval_required: e.target.checked })} />Require approval</label>
      </div>
      <div className="flex">
        <div className="min-w-0 flex-1"><WorkflowCanvas workflow={workflow} onSelect={setSelectedNodeId} onReload={() => workflow && load(workflow.id)} /></div>
        <CardConfigPanel node={selectedNode} onRefresh={() => workflow && load(workflow.id)} />
      </div>
      <div className="flex items-center gap-2 rounded-xl border border-white/10 bg-slate-950/70 p-3 text-xs text-slate-300"><ShieldAlert size={16} className="text-amber-200" />Phase 3 default is read-only and approval-first. Login, MFA, CAPTCHA, password entry, and destructive actions are blocked.</div>
    </div>
  );
}
