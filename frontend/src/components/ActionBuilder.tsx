import { Plus, ShieldCheck } from "lucide-react";
import { createAction, updateAction } from "../api/client";
import type { CardAction, CardActionType, WorkflowNode } from "../types";

const actionTypes: CardActionType[] = ["wait", "click_by_image", "click_by_text", "click_by_coordinates", "type_text", "press_key", "hotkey", "scroll", "wait_for_image", "wait_for_text", "take_screenshot", "extract_text", "download_wait", "upload_file", "read_file", "clean_file", "save_to_database", "run_sql", "generate_excel", "generate_pdf", "human_approval", "final_answer"];
const guiActions = new Set(["click_by_image", "click_by_text", "click_by_coordinates", "type_text", "press_key", "hotkey", "scroll", "wait_for_image", "wait_for_text", "take_screenshot", "extract_text"]);

export default function ActionBuilder({ node, onChanged }: { node: WorkflowNode; onChanged: () => void }) {
  async function add(type: CardActionType) {
    await createAction(node.id, type, (node.actions?.length || 0) + 1);
    onChanged();
  }
  async function patch(action: CardAction, payload: Record<string, unknown>) {
    await updateAction(action.id, payload);
    onChanged();
  }
  function config(action: CardAction) {
    return action.action_config_json || {};
  }
  return (
    <div className="space-y-3">
      <select className="field" onChange={(event) => add(event.target.value as CardActionType)} defaultValue="">
        <option value="" disabled>Add action</option>
        {actionTypes.map((type) => <option key={type} value={type}>{type}</option>)}
      </select>
      <div className="space-y-3">
        {node.actions?.map((action) => (
          <div key={action.id} className="rounded-lg border border-white/10 bg-white/5 p-3 text-xs">
            <div className="flex items-center justify-between">
              <span>{action.action_order}. {action.action_type}</span>
              <span className="text-slate-400">{action.timeout_seconds}s / retry {action.retry_count}</span>
            </div>
            <div className="mt-3 grid gap-2">
              <label className="flex items-center gap-2 text-slate-300"><input type="checkbox" checked={!!action.approved_for_execution} onChange={(e) => patch(action, { approved_for_execution: e.target.checked })} /> approved_for_execution</label>
              <label className="flex items-center gap-2 text-slate-300"><input type="checkbox" checked={!!action.requires_gui_control || guiActions.has(action.action_type)} onChange={(e) => patch(action, { requires_gui_control: e.target.checked })} /> requires_gui_control</label>
              <input className="field" placeholder="reference screenshot path" value={String(config(action).reference_screenshot || config(action).path || "")} onChange={(e) => patch(action, { action_config_json: { ...config(action), reference_screenshot: e.target.value } })} />
              <div className="grid grid-cols-2 gap-2">
                <input className="field" type="number" step="0.01" placeholder="confidence" value={String(config(action).confidence_threshold || "")} onChange={(e) => patch(action, { action_config_json: { ...config(action), confidence_threshold: Number(e.target.value) } })} />
                <input className="field" type="number" placeholder="timeout" value={action.timeout_seconds} onChange={(e) => patch(action, { timeout_seconds: Number(e.target.value) })} />
              </div>
              {action.action_type === "click_by_coordinates" && <label className="flex items-center gap-2 text-amber-200"><input type="checkbox" checked={!!config(action).coordinate_warning_accepted} onChange={(e) => patch(action, { action_config_json: { ...config(action), coordinate_warning_accepted: e.target.checked } })} /> coordinate warning accepted</label>}
              <textarea className="field min-h-16" placeholder="Safety notes" value={action.safety_notes || ""} onChange={(e) => patch(action, { safety_notes: e.target.value })} />
            </div>
          </div>
        ))}
        {!node.actions?.length && <div className="flex items-center gap-2 text-xs text-slate-400"><Plus size={14} />No actions configured.</div>}
      </div>
      <div className="flex items-center gap-2 rounded-lg border border-amber-300/20 bg-amber-300/10 p-3 text-xs text-amber-100"><ShieldCheck size={15} />GUI actions remain approval-first and destructive actions are blocked.</div>
    </div>
  );
}
