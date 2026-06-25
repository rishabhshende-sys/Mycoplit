import { Background, Connection, Controls, MiniMap, Node, NodeMouseHandler, ReactFlow, addEdge, useEdgesState, useNodesState } from "reactflow";
import { useCallback, useEffect } from "react";
import type { Workflow, WorkflowNodeType } from "../types";
import AutomationCard from "./AutomationCard";
import { createEdge, createNode, updateNode } from "../api/client";

const nodeTypes = { automationCard: AutomationCard };

export default function WorkflowCanvas({ workflow, onSelect, onReload }: { workflow?: Workflow; onSelect: (id: number) => void; onReload: () => void }) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    if (!workflow) return;
    setNodes(workflow.nodes.map((node) => ({
      id: String(node.id),
      type: "automationCard",
      position: { x: node.position_x, y: node.position_y },
      data: {
        ...node,
        id: node.id,
        status: workflow.status,
        screenshotCount: node.screenshots?.length || 0,
        actionCount: node.actions?.length || 0,
        onConfigure: onSelect,
      },
    })));
    setEdges(workflow.edges.map((edge) => ({
      id: String(edge.id),
      source: String(edge.source_node_id),
      target: String(edge.target_node_id),
      animated: true,
      style: { stroke: "#67e8f9" },
    })));
  }, [workflow, setNodes, setEdges, onSelect]);

  const onConnect = useCallback(async (connection: Connection) => {
    if (!workflow || !connection.source || !connection.target) return;
    setEdges((eds) => addEdge({ ...connection, animated: true }, eds));
    await createEdge(workflow.id, Number(connection.source), Number(connection.target));
    onReload();
  }, [workflow, setEdges, onReload]);

  const onDragStop = useCallback(async (_: unknown, node: Node) => {
    if (!workflow) return;
    await updateNode(workflow.id, Number(node.id), { position_x: node.position.x, position_y: node.position.y });
  }, [workflow]);

  async function addCard(type: WorkflowNodeType) {
    if (!workflow) return;
    await createNode(workflow.id, {
      node_type: type,
      card_name: type,
      description: "",
      instruction_text: "",
      position_x: 120 + workflow.nodes.length * 32,
      position_y: 160 + workflow.nodes.length * 18,
      config_json: { mode: "read-only", execute: false },
    });
    onReload();
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] overflow-hidden rounded-xl border border-white/10 bg-slate-950/45">
      <aside className="w-64 border-r border-white/10 p-4">
        <p className="mb-3 text-xs uppercase tracking-[0.2em] text-cyan-200">Card templates</p>
        <div className="space-y-2">
          {["START", "GUI Screen Step", "Browser Step", "Desktop App Step", "File Step", "Database Step", "Validation Step", "Analysis Step", "Report Step", "Human Approval Step", "END"].map((type) => (
            <button key={type} onClick={() => addCard(type as WorkflowNodeType)} className="w-full rounded-lg border border-white/10 bg-white/5 px-3 py-2 text-left text-xs text-slate-200 hover:bg-cyan-400/10">{type}</button>
          ))}
        </div>
      </aside>
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={((_, node) => onSelect(Number(node.id))) as NodeMouseHandler}
          onNodeDragStop={onDragStop}
          fitView
        >
          <Background color="#164e63" gap={24} />
          <MiniMap nodeColor="#22d3ee" maskColor="rgba(2, 6, 23, 0.72)" />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}
