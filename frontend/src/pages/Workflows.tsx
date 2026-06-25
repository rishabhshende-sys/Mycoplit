import { useEffect, useState } from "react";
import { createWorkflow, deleteWorkflow, getWorkflows } from "../api/client";
import type { Workflow } from "../types";

export default function Workflows({ openBuilder }: { openBuilder: (id: number) => void }) {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [name, setName] = useState("New Visual Workflow");
  const load = () => getWorkflows().then(setWorkflows);
  useEffect(() => {
    void load();
  }, []);

  async function create() {
    const workflow = await createWorkflow(name);
    await load();
    openBuilder(workflow.id);
  }

  async function remove(id: number) {
    await deleteWorkflow(id);
    load();
  }

  return (
    <div className="space-y-5">
      <h2 className="text-2xl font-semibold">Workflows</h2>
      <div className="flex gap-3">
        <input className="field max-w-md" value={name} onChange={(event) => setName(event.target.value)} />
        <button className="btn" onClick={create}>Create workflow</button>
      </div>
      <div className="grid gap-3">
        {workflows.map((workflow) => (
          <div key={workflow.id} className="panel flex items-center justify-between">
            <div><h3 className="font-semibold">{workflow.name}</h3><p className="text-sm text-slate-400">{workflow.nodes.length} cards - {workflow.edges.length} wires</p></div>
            <div className="flex gap-2"><button className="btn" onClick={() => openBuilder(workflow.id)}>Open</button><button className="btn-danger" onClick={() => remove(workflow.id)}>Delete</button></div>
          </div>
        ))}
      </div>
    </div>
  );
}
