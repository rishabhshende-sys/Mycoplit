import { create } from "zustand";

interface WorkflowCanvasState {
  selectedNodeId?: number;
  activeWorkflowId?: number;
  setSelectedNodeId: (id?: number) => void;
  setActiveWorkflowId: (id?: number) => void;
}

export const useWorkflowStore = create<WorkflowCanvasState>((set) => ({
  selectedNodeId: undefined,
  activeWorkflowId: undefined,
  setSelectedNodeId: (selectedNodeId) => set({ selectedNodeId }),
  setActiveWorkflowId: (activeWorkflowId) => set({ activeWorkflowId }),
}));
