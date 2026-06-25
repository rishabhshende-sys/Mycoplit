export default function Settings() {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-semibold">Settings</h2>
      <div className="panel space-y-3 text-sm text-slate-300">
        <p>Project mode: read-only</p>
        <p>GUI automation execution: disabled in Phase 1</p>
        <p>External portal integrations: disabled in Phase 1</p>
        <p>Credentials are not stored or hardcoded.</p>
      </div>
    </div>
  );
}
