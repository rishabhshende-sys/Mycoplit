export type WorkflowNodeType =
  | "START"
  | "GUI Screen Step"
  | "Browser Step"
  | "Desktop App Step"
  | "File Step"
  | "Database Step"
  | "Validation Step"
  | "Analysis Step"
  | "Report Step"
  | "Human Approval Step"
  | "END";

export type CardActionType =
  | "wait"
  | "click_by_image"
  | "click_by_text"
  | "click_by_coordinates"
  | "type_text"
  | "press_key"
  | "hotkey"
  | "scroll"
  | "wait_for_image"
  | "wait_for_text"
  | "take_screenshot"
  | "extract_text"
  | "download_wait"
  | "upload_file"
  | "read_file"
  | "clean_file"
  | "save_to_database"
  | "run_sql"
  | "generate_excel"
  | "generate_pdf"
  | "human_approval"
  | "final_answer";

export interface CardAction {
  id: number;
  node_id: number;
  action_order: number;
  action_type: CardActionType;
  action_config_json: Record<string, unknown>;
  timeout_seconds: number;
  retry_count: number;
  approved_for_execution: boolean;
  requires_gui_control: boolean;
  safety_notes?: string;
  created_at: string;
}

export interface CardScreenshot {
  id: number;
  node_id: number;
  screenshot_type: string;
  file_path: string;
  description?: string;
  expected_text?: string;
  crop_json: Record<string, unknown>;
  confidence_threshold: number;
  created_at: string;
}

export interface WorkflowNode {
  id: number;
  workflow_id: number;
  node_type: WorkflowNodeType;
  card_name: string;
  description?: string;
  instruction_text?: string;
  position_x: number;
  position_y: number;
  config_json: Record<string, unknown>;
  allow_skip_on_failure: boolean;
  human_approval_required: boolean;
  screenshots: CardScreenshot[];
  actions: CardAction[];
}

export interface WorkflowEdge {
  id: number;
  workflow_id: number;
  source_node_id: number;
  target_node_id: number;
  condition_json: Record<string, unknown>;
}

export interface Workflow {
  id: number;
  name: string;
  description?: string;
  trigger_keywords?: string;
  status: string;
  gui_actions_enabled: boolean;
  approval_required: boolean;
  created_at: string;
  updated_at: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface AuditLog {
  id: number;
  user_id?: number;
  action: string;
  entity_type: string;
  entity_id?: number;
  details?: string;
  created_at: string;
}
