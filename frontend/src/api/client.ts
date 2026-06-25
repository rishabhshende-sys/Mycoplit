import axios from "axios";
import type { CardActionType, Workflow } from "../types";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
});

export const getWorkflows = async () => (await api.get<Workflow[]>("/api/workflows")).data;
export const getWorkflow = async (id: number) => (await api.get<Workflow>(`/api/workflows/${id}`)).data;
export const createWorkflow = async (name: string) =>
  (await api.post<Workflow>("/api/workflows", { name, description: "", status: "draft" })).data;
export const updateWorkflow = async (id: number, data: Partial<Workflow>) =>
  (await api.put<Workflow>(`/api/workflows/${id}`, data)).data;
export const deleteWorkflow = async (id: number) => api.delete(`/api/workflows/${id}`);

export const createNode = async (workflowId: number, payload: Record<string, unknown>) =>
  (await api.post(`/api/workflows/${workflowId}/nodes`, payload)).data;
export const updateNode = async (workflowId: number, nodeId: number, payload: Record<string, unknown>) =>
  (await api.put(`/api/workflows/${workflowId}/nodes/${nodeId}`, payload)).data;
export const deleteNode = async (workflowId: number, nodeId: number) =>
  api.delete(`/api/workflows/${workflowId}/nodes/${nodeId}`);

export const createEdge = async (workflowId: number, source_node_id: number, target_node_id: number) =>
  (await api.post(`/api/workflows/${workflowId}/edges`, { source_node_id, target_node_id, condition_json: { on: "success" } })).data;
export const deleteEdge = async (workflowId: number, edgeId: number) =>
  api.delete(`/api/workflows/${workflowId}/edges/${edgeId}`);

export const uploadScreenshot = async (nodeId: number, form: FormData) =>
  (await api.post(`/api/nodes/${nodeId}/screenshots`, form)).data;

export const createAction = async (nodeId: number, action_type: CardActionType, action_order: number) =>
  (await api.post(`/api/nodes/${nodeId}/actions`, {
    action_order,
    action_type,
    action_config_json: { execute: false },
    timeout_seconds: 30,
    retry_count: 0,
  })).data;

export const runChat = async (payload: Record<string, unknown>) => (await api.post("/api/chat/run", payload)).data;
export const runWorkflow = async (workflowId: number, payload: Record<string, unknown>) => (await api.post(`/api/workflows/${workflowId}/run`, payload)).data;
export const getRunNodes = async (runId: number) => (await api.get(`/api/workflow-runs/${runId}/nodes`)).data;
export const getRunActions = async (runId: number) => (await api.get(`/api/workflow-runs/${runId}/actions`)).data;
export const getRunEvents = async (runId: number) => (await api.get(`/api/workflow-runs/${runId}/events`)).data;
export const stopRun = async (runId: number) => (await api.post(`/api/workflow-runs/${runId}/stop`)).data;
export const getFiles = async () => (await api.get("/api/files")).data;
export const inspectFile = async (fileId: number) => (await api.post(`/api/files/${fileId}/inspect`)).data;
export const getReports = async () => (await api.get("/api/reports")).data;
export const updateAction = async (actionId: number, payload: Record<string, unknown>) => (await api.put(`/api/actions/${actionId}`, payload)).data;
export const approveNodeRun = async (nodeRunId: number) => (await api.post(`/api/node-runs/${nodeRunId}/approve`)).data;
export const rejectNodeRun = async (nodeRunId: number) => (await api.post(`/api/node-runs/${nodeRunId}/reject`)).data;
export const skipNodeRun = async (nodeRunId: number) => (await api.post(`/api/node-runs/${nodeRunId}/skip`)).data;
export const testScreenshot = async () => (await api.post("/api/vision/test-screenshot")).data;
export const testMatchTemplate = async (payload: Record<string, unknown>) => (await api.post("/api/vision/match-template", payload)).data;
export const testOcr = async (payload: Record<string, unknown>) => (await api.post("/api/vision/test-ocr", payload)).data;
