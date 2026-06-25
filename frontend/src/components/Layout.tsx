import { Activity, Bot, FileSpreadsheet, GitBranch, LayoutDashboard, MonitorDot, ScrollText, Settings } from "lucide-react";
import type { ReactNode } from "react";

const nav = [
  ["Dashboard", "dashboard", LayoutDashboard],
  ["Workflows", "workflows", GitBranch],
  ["Chatbot", "chatbot", Bot],
  ["Run Monitor", "monitor", MonitorDot],
  ["Files", "files", FileSpreadsheet],
  ["Reports", "reports", ScrollText],
  ["Flow Builder", "builder", Activity],
  ["Audit Logs", "audit", ScrollText],
  ["Settings", "settings", Settings],
] as const;

export default function Layout({ page, setPage, children }: { page: string; setPage: (page: string) => void; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,#1f6f8b_0,#08111f_34%,#030712_100%)] text-slate-100">
      <aside className="fixed inset-y-0 left-0 z-20 w-64 border-r border-white/10 bg-slate-950/70 p-5 backdrop-blur-xl">
        <div className="mb-8">
          <p className="text-xs uppercase tracking-[0.24em] text-cyan-200">Mycoplit</p>
          <h1 className="mt-2 text-xl font-semibold">Visual AI Command Center</h1>
        </div>
        <nav className="space-y-2">
          {nav.map(([label, key, Icon]) => (
            <button key={key} onClick={() => setPage(key)} className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm ${page === key ? "bg-cyan-400/15 text-cyan-100" : "text-slate-300 hover:bg-white/8"}`}>
              <Icon size={17} />
              {label}
            </button>
          ))}
        </nav>
      </aside>
      <main className="ml-64 min-h-screen p-6">{children}</main>
    </div>
  );
}
