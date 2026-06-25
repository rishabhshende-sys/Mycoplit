# Mycoplit Visual AI Command Center

Mycoplit is a visual automation workflow builder and command center. Phase 1 provides the Figma-like workflow canvas, saved workflow templates, card configuration, screenshot metadata, action configuration, and audit logs. Phase 2 adds a safe local workflow execution engine for file/database/report actions without controlling any external GUI.

GUI automation remains disabled until Phase 3. Phase 2 does not execute mouse, keyboard, browser, desktop, SAP, portal, login, MFA, CAPTCHA, DRM, or access-control automation.

## Phase 1 Scope

- FastAPI backend with SQLite, SQLAlchemy, Pydantic, CORS, startup table creation, and seed data.
- Workflow, card/node, edge/wire, screenshot metadata, action configuration, and audit log APIs.
- React/Vite/TypeScript frontend with Tailwind CSS, React Flow, and Zustand canvas state.
- Dashboard, Workflows list, Flow Builder, card configuration panel, screenshot upload, action builder, settings, and audit logs.
- Default mode is read-only for GUI automation actions.

## Phase 2 Scope

- DAG workflow runner with `workflow_runs`, `node_runs`, `action_runs`, and `workflow_events` audit trail.
- Chatbot trigger endpoint with lightweight Boss Agent workflow selection and variable extraction.
- Server-Sent Events live progress stream for card-by-card thinking and execution status.
- Safe executable actions: `wait`, `read_file`, `clean_file`, `save_to_database`, `run_sql`, `generate_excel`, `generate_pdf`, `human_approval`, and `final_answer`.
- Safe placeholders for GUI actions. They return: `GUI automation action is configured but not executable until Phase 3.`
- CSV/XLSX inspection, cleaning, duplicate-aware import into local SQLite `sales_fact`, sales analysis, Excel report, PDF report, and final answer generation.

## Backend Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend URL: `http://localhost:8000`

Health check: `http://localhost:8000/health`

## Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Run The Sample File Workflow

1. Start the backend and frontend.
2. Open the Chatbot page.
3. Select `Demo File Analysis Flow`, or leave workflow selection on auto.
4. Send: `sale nikal customer Acme Traders June 2021 se current date tak`.
5. Watch the Thinking Panel update each card through START, sample CSV selection, read, clean, database save, SQL/Python summary, Excel report, PDF report, final answer, and END.

The seeded sample file is stored at `backend/app/storage/uploads/sample_sales.csv` after startup. It contains multiple customers, multiple months and years, one duplicate row, one missing `material_name`, and one negative `net_value` for validation coverage.

## Chatbot And SSE Progress

`POST /api/chat/run` accepts `user_message`, optional `workflow_id`, and optional `variables`. It returns a `run_id`, selected workflow, and initial status.

The frontend then connects to:

```text
GET /api/workflow-runs/{run_id}/stream
```

The SSE stream emits workflow, node, and action events so the Thinking Panel and Run Monitor can show active, completed, failed, and waiting cards in real time.

## Files, Data Import, And Reports

Files can be uploaded and inspected through the Files page or `/api/files` endpoints. CSV/XLSX files are read with pandas, common sales columns are mapped, dates and numeric values are normalized, blank rows are removed, and cleaned CSVs are written to `backend/app/storage/cleaned`.

Cleaned sales rows are imported into local SQLite table `sales_fact`. Duplicates are avoided using `invoice_no + invoice_date + customer_code + material_code`.

Reports are generated under `backend/app/storage/reports`:

- Excel reports use `openpyxl`.
- PDF reports use a local dependency-free MVP PDF writer.
- Report metadata is saved in the `reports` table and downloadable from the Reports page.

## Safety Notes

- Authorized internal office workflows only.
- GUI automation is still disabled until Phase 3.
- No `pyautogui` mouse or keyboard control is used in Phase 2.
- No external portal or desktop application is controlled in Phase 2.
- GUI actions are placeholders and are audit logged when encountered.
- Workflow runs, node runs, action runs, file uploads, imports, reports, final answers, stops, retries, and failures are audit/event logged.


## Phase 3 Scope

Phase 3 adds screenshot-based GUI detection and approval-first GUI action execution on top of the Phase 1/2 workflow builder. The default remains read-only. GUI actions only run when the workflow is enabled for GUI actions, the action is approved for execution, and any required human approval has been granted.

### Screenshot Detection

Current screen capture is available through `POST /api/vision/test-screenshot` and the `take_screenshot` action. Captured run screenshots are stored under `backend/app/storage/screenshots/runs` and shown in Run Monitor.

Template matching uses OpenCV when installed. `POST /api/vision/match-template` accepts a `reference_screenshot` path and optionally a `current_screenshot` path. If no current screenshot is provided, the backend captures the current screen first. The response includes `match_found`, `confidence`, `bounding_box`, `center_x`, and `center_y` when a match can be evaluated.

### Reference Screenshots

Upload screenshots from the card Screenshots tab and mark them as `before`, `target`, `success`, or `error`. For `click_by_image` and `wait_for_image`, configure the action `reference_screenshot` path from the uploaded screenshot. Set `confidence_threshold` per action; `0.8` is the default starting point.

### GUI Action Safety

Workflow-level settings are in Flow Builder:

- Enable GUI actions for this workflow
- Require approval before GUI actions

Card/action-level settings are in Card Config Panel:

- `approved_for_execution`
- `requires_gui_control`
- coordinate warning acceptance for coordinate clicks
- confidence threshold
- timeout seconds
- reference screenshot path

Before any mouse or keyboard action, the backend checks workflow, node, and action approval gates. If approval is required, the workflow pauses and emits an `approval_required` SSE event. Run Monitor shows Approve once, Reject, and Stop workflow.

### Emergency Stop, Retry, And Skip

`POST /api/workflow-runs/{run_id}/stop` sets a stop flag. The execution engine checks that flag before each action and marks the workflow stopped.

Run Monitor exposes retry, skip, and stop controls. Skip is allowed only when the node has `allow_skip_on_failure=true`. Retry is audit-logged in this MVP and can be expanded into full node replay later.

### OCR

OCR is optional. `click_by_text`, `wait_for_text`, and `extract_text` use `pytesseract` if configured. If OCR is not available, the backend returns the controlled message: `OCR engine not configured.`

### Coordinate Clicks

Coordinate clicks are fragile because screen resolution, browser zoom, app layout, and monitor placement can change. They are blocked unless `coordinate_warning_accepted=true`. Prefer image matching with approval.

### Hard Safety Blocks

Phase 3 blocks password/MFA/OTP/CAPTCHA automation and destructive external actions. Keywords such as delete, remove, submit, post, approve, reject, cancel, transfer, payment, save changes, and update record are blocked. Future SAP/portal integration should use explicit connector permissions, read-only defaults, and separate safe-write mode rather than direct uncontrolled GUI automation.
