import { useState } from "react";
import { testMatchTemplate, testOcr, testScreenshot, updateNode } from "../api/client";
import type { WorkflowNode, WorkflowNodeType } from "../types";
import ActionBuilder from "./ActionBuilder";
import ScreenshotUploader from "./ScreenshotUploader";

const tabs = ["Node Settings", "Screenshots", "Actions", "Detection", "Success/Failure", "Advanced"];
const nodeTypes: WorkflowNodeType[] = ["START", "GUI Screen Step", "Browser Step", "Desktop App Step", "File Step", "Database Step", "Validation Step", "Analysis Step", "Report Step", "Human Approval Step", "END"];

export default function CardConfigPanel({ node, onRefresh }: { node?: WorkflowNode; onRefresh: () => void }) {
  const [tab, setTab] = useState(tabs[0]);
  const [detection, setDetection] = useState<any>();
  if (!node) return <aside className="w-96 border-l border-white/10 bg-slate-950/75 p-5 text-sm text-slate-400 backdrop-blur-xl">Select a card to configure it.</aside>;
  const activeNode = node;

  async function save(field: string, value: unknown) {
    await updateNode(activeNode.workflow_id, activeNode.id, { [field]: value });
    onRefresh();
  }
  async function runMatch() {
    const reference = activeNode.screenshots?.find((s) => s.screenshot_type === "target") || activeNode.screenshots?.[0];
    if (!reference) { setDetection({ error: "Upload a target screenshot first." }); return; }
    setDetection(await testMatchTemplate({ reference_screenshot: reference.file_path }));
  }
  async function runOcr() {
    const shot = activeNode.screenshots?.[0];
    setDetection(await testOcr({ screenshot: shot?.file_path, expected_text: shot?.expected_text }));
  }
  async function capture() {
    setDetection(await testScreenshot());
  }

  return (
    <aside className="w-96 overflow-y-auto border-l border-white/10 bg-slate-950/75 p-5 backdrop-blur-xl">
      <h2 className="text-lg font-semibold text-white">{activeNode.card_name}</h2>
      <div className="mt-4 grid grid-cols-2 gap-2">
        {tabs.map((item) => <button key={item} onClick={() => setTab(item)} className={`rounded-lg px-3 py-2 text-xs ${tab === item ? "bg-cyan-400/15 text-cyan-100" : "bg-white/5 text-slate-300"}`}>{item}</button>)}
      </div>
      <div className="mt-5 space-y-3">
        {tab === "Node Settings" && <>
          <input className="field" value={activeNode.card_name} onChange={(event) => save("card_name", event.target.value)} />
          <select className="field" value={activeNode.node_type} onChange={(event) => save("node_type", event.target.value)}>{nodeTypes.map((type) => <option key={type}>{type}</option>)}</select>
          <textarea className="field min-h-20" placeholder="Description" value={activeNode.description || ""} onChange={(event) => save("description", event.target.value)} />
          <textarea className="field min-h-28" placeholder="Instruction text" value={activeNode.instruction_text || ""} onChange={(event) => save("instruction_text", event.target.value)} />
        </>}
        {tab === "Screenshots" && <ScreenshotUploader node={activeNode} onUploaded={onRefresh} />}
        {tab === "Actions" && <ActionBuilder node={activeNode} onChanged={onRefresh} />}
        {tab === "Detection" && <div className="space-y-3">
          <button className="w-full rounded-lg bg-cyan-300 px-3 py-2 font-semibold text-slate-950" onClick={capture}>Capture current screen</button>
          <button className="w-full rounded-lg border border-cyan-300/30 px-3 py-2 text-cyan-100" onClick={runMatch}>Test image match</button>
          <button className="w-full rounded-lg border border-amber-300/30 px-3 py-2 text-amber-100" onClick={runOcr}>Test OCR</button>
          {detection && <pre className="max-h-80 overflow-auto rounded-lg bg-slate-900 p-3 text-xs text-slate-200">{JSON.stringify(detection, null, 2)}</pre>}
        </div>}
        {tab === "Success/Failure" && <textarea className="field min-h-40" defaultValue={JSON.stringify(activeNode.config_json?.outcomes || {}, null, 2)} />}
        {tab === "Advanced" && <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={!!activeNode.human_approval_required} onChange={(e) => save("human_approval_required", e.target.checked)} />Human approval required</label>
          <label className="flex items-center gap-2 text-sm text-slate-300"><input type="checkbox" checked={!!activeNode.allow_skip_on_failure} onChange={(e) => save("allow_skip_on_failure", e.target.checked)} />Allow skip on failure</label>
          <div className="rounded-lg border border-amber-300/20 bg-amber-300/10 p-3 text-xs text-amber-100">Coordinate clicks are fragile. Prefer image matching and approval-first actions.</div>
        </div>}
      </div>
    </aside>
  );
}
