import { useState } from "react";
import Layout from "./components/Layout";
import AuditLogs from "./pages/AuditLogs";
import Chatbot from "./pages/Chatbot";
import Dashboard from "./pages/Dashboard";
import Files from "./pages/Files";
import FlowBuilder from "./pages/FlowBuilder";
import Reports from "./pages/Reports";
import RunMonitor from "./pages/RunMonitor";
import Settings from "./pages/Settings";
import Workflows from "./pages/Workflows";

export default function App() {
  const [page, setPage] = useState("dashboard");
  const [activeWorkflowId, setActiveWorkflowId] = useState<number>();
  function openBuilder(id: number) {
    setActiveWorkflowId(id);
    setPage("builder");
  }
  return (
    <Layout page={page} setPage={setPage}>
      {page === "dashboard" && <Dashboard />}
      {page === "chatbot" && <Chatbot />}
      {page === "monitor" && <RunMonitor />}
      {page === "files" && <Files />}
      {page === "reports" && <Reports />}
      {page === "workflows" && <Workflows openBuilder={openBuilder} />}
      {page === "builder" && <FlowBuilder activeWorkflowId={activeWorkflowId} />}
      {page === "audit" && <AuditLogs />}
      {page === "settings" && <Settings />}
    </Layout>
  );
}
