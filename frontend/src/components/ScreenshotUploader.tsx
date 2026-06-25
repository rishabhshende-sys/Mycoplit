import { useState } from "react";
import { uploadScreenshot } from "../api/client";
import type { WorkflowNode } from "../types";

const types = ["before", "target", "success", "error"];

export default function ScreenshotUploader({ node, onUploaded }: { node: WorkflowNode; onUploaded: () => void }) {
  const [type, setType] = useState("target");
  const [description, setDescription] = useState("");
  const [expectedText, setExpectedText] = useState("");
  const [confidence, setConfidence] = useState(0.8);

  async function submit(file?: File) {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    form.append("screenshot_type", type);
    form.append("description", description);
    form.append("expected_text", expectedText);
    form.append("confidence_threshold", String(confidence));
    await uploadScreenshot(node.id, form);
    onUploaded();
  }

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <select className="field" value={type} onChange={(event) => setType(event.target.value)}>
          {types.map((item) => <option key={item}>{item}</option>)}
        </select>
        <input className="field" type="number" min="0" max="1" step="0.05" value={confidence} onChange={(event) => setConfidence(Number(event.target.value))} />
      </div>
      <input className="field" placeholder="Description" value={description} onChange={(event) => setDescription(event.target.value)} />
      <input className="field" placeholder="Expected text" value={expectedText} onChange={(event) => setExpectedText(event.target.value)} />
      <input className="field" type="file" accept="image/*" onChange={(event) => submit(event.target.files?.[0])} />
      <div className="space-y-2 text-xs text-slate-300">
        {node.screenshots?.map((shot) => (
          <div key={shot.id} className="rounded-lg border border-white/10 bg-white/5 p-2">
            {shot.screenshot_type} - {shot.description || "uploaded"}
          </div>
        ))}
      </div>
    </div>
  );
}
