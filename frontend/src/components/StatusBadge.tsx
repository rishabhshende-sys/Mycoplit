export default function StatusBadge({ status = "draft" }: { status?: string }) {
  const tone = status === "active" ? "bg-emerald-400/15 text-emerald-200" : "bg-sky-400/15 text-sky-200";
  return <span className={`rounded-full px-2 py-1 text-[11px] font-medium ${tone}`}>{status}</span>;
}
