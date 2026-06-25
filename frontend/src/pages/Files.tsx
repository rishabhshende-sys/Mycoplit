import { useEffect, useState } from "react";
import { FileSearch } from "lucide-react";
import { getFiles, inspectFile } from "../api/client";

export default function Files() {
  const [files, setFiles] = useState<any[]>([]);
  const [preview, setPreview] = useState<any>();
  useEffect(() => { getFiles().then(setFiles); }, []);
  return <div className="grid gap-5 lg:grid-cols-[360px_1fr]">
    <section className="rounded-xl border border-white/10 bg-slate-950/60 p-5"><h1 className="text-2xl font-semibold">Files</h1><div className="mt-4 space-y-3">{files.map((file) => <button key={file.id} onClick={async () => setPreview(await inspectFile(file.id))} className="flex w-full items-center justify-between rounded-lg border border-white/10 bg-white/5 p-3 text-left"><span>{file.original_name}</span><FileSearch size={18} /></button>)}</div></section>
    <section className="rounded-xl border border-white/10 bg-slate-950/60 p-5"><h2 className="font-semibold">Preview</h2>{preview && <><p className="mt-2 text-sm text-slate-300">Rows: {preview.row_count}</p><p className="mt-2 text-sm text-cyan-200">{preview.columns?.join(", ")}</p><pre className="mt-4 max-h-96 overflow-auto rounded-lg bg-slate-900 p-4 text-xs">{JSON.stringify(preview.sample_rows, null, 2)}</pre></>}</section>
  </div>;
}
