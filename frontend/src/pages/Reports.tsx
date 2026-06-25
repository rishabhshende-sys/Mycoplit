import { useEffect, useState } from "react";
import { Download } from "lucide-react";
import { getReports } from "../api/client";

export default function Reports() {
  const [reports, setReports] = useState<any[]>([]);
  useEffect(() => { getReports().then(setReports); }, []);
  const base = import.meta.env.VITE_API_URL || "http://localhost:8000";
  return <div className="space-y-4"><h1 className="text-2xl font-semibold">Reports</h1>{reports.map((report) => <div key={report.id} className="flex items-center justify-between rounded-xl border border-white/10 bg-slate-950/60 p-4"><div><p className="font-semibold uppercase text-cyan-100">{report.report_type}</p><p className="text-sm text-slate-300">{report.summary}</p></div><a className="flex items-center gap-2 rounded-lg bg-cyan-300 px-4 py-2 text-slate-950" href={`${base}${report.download_url}`}><Download size={16} /> Download</a></div>)}</div>;
}
