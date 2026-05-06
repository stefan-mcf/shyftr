import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, DEFAULT_ROOT, Json } from "./api";
import "./styles.css";

const nav = ["Cells", "Review", "Charges", "Packs", "Signal", "Frontier", "Multi-cell", "Reports", "Settings"] as const;
type Tab = typeof nav[number];

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json">{JSON.stringify(value, null, 2)}</pre>;
}

function Card({ label, value }: { label: string; value: unknown }) {
  return <section className="card"><span>{label}</span><strong>{String(value ?? 0)}</strong></section>;
}

function App() {
  const [tab, setTab] = useState<Tab>("Cells");
  const [root, setRoot] = useState(DEFAULT_ROOT);
  const [cellId, setCellId] = useState("");
  const [cells, setCells] = useState<Json[]>([]);
  const [summary, setSummary] = useState<Json | null>(null);
  const [rows, setRows] = useState<Json | null>(null);
  const [query, setQuery] = useState("memory pilot");
  const [pack, setPack] = useState<Json | null>(null);
  const [signal, setSignal] = useState<Json | null>(null);
  const [configPath, setConfigPath] = useState("");
  const [targetId, setTargetId] = useState("");
  const [rationale, setRationale] = useState("");
  const [actionResult, setActionResult] = useState<Json | null>(null);
  const [raw, setRaw] = useState(false);
  const [registryPath, setRegistryPath] = useState("./ledger/cell_registry.jsonl");
  const [crossCellIds, setCrossCellIds] = useState("");
  const [retrievalMode, setRetrievalMode] = useState("balanced");
  const [proposedMode, setProposedMode] = useState("conservative");
  const [simulation, setSimulation] = useState<Json | null>(null);
  const [error, setError] = useState("");

  async function run<T>(fn: () => Promise<T>): Promise<T | undefined> {
    setError("");
    try { return await fn(); } catch (err) { setError(err instanceof Error ? err.message : String(err)); }
  }

  async function refreshCells() {
    const payload = await run(() => api.cells(root));
    if (!payload) return;
    setCells(payload.cells as unknown as Json[]);
    const first = (payload.cells[0]?.cell_id || "") as string;
    if (!cellId && first) setCellId(first);
  }

  async function refreshSummary(selected = cellId) {
    if (!selected) return;
    const payload = await run(() => api.summary(root, selected));
    if (payload) setSummary(payload as unknown as Json);
  }

  useEffect(() => { refreshCells(); }, []);
  useEffect(() => { if (cellId) refreshSummary(cellId); }, [cellId]);

  const counts = (summary?.counts || {}) as Record<string, number>;

  async function loadTab(target: Tab = tab) {
    if (!cellId) return;
    const loaders: Partial<Record<Tab, () => Promise<Json>>> = {
      Review: () => api.sparks(root, cellId),
      Charges: () => api.charges(root, cellId, query),
      Reports: async () => ({
        hygiene: await api.hygiene(root, cellId),
        sweep: await api.sweep(root, cellId),
        proposals: await api.proposals(root, cellId),
        metrics: await api.metrics(root, cellId),
        operator_burden: await api.burden(root, cellId),
        policy_tuning: await api.policy(root, cellId),
      }),
      Frontier: () => api.frontier(String(selectedCell?.cell_path || summary?.cell_path || "")),
    };
    const loader = loaders[target];
    if (!loader) return;
    const payload = await run(loader);
    if (payload) setRows(payload);
  }

  const selectedCell = useMemo(() => cells.find((c) => c.cell_id === cellId), [cells, cellId]);

  return <main>
    <header>
      <div><h1>ShyftR Console</h1><p>Local-first Cell dashboard, review queue, Pack debugger, Signal console, and pilot metrics.</p></div>
      <button onClick={() => { refreshCells(); refreshSummary(); }}>Refresh</button>
    </header>
    {error && <div className="error">{error}</div>}
    <section className="settings">
      <label>Cell root <input value={root} onChange={(e) => setRoot(e.target.value)} /></label>
      <label>Cell <select value={cellId} onChange={(e) => setCellId(e.target.value)}>{cells.map((c) => <option key={String(c.cell_id)} value={String(c.cell_id)}>{String(c.cell_id)}</option>)}</select></label>
      <label><input type="checkbox" checked={raw} onChange={(e) => setRaw(e.target.checked)} /> JSON inspect</label>
    </section>
    <nav>{nav.map((item) => <button key={item} className={tab === item ? "active" : ""} onClick={() => { setTab(item); setRows(null); setTimeout(() => loadTab(item), 0); }}>{item}</button>)}</nav>

    {tab === "Cells" && <section>
      <h2>Cell Dashboard</h2>
      <div className="cards">
        <Card label="Pulses" value={counts.pulses} /><Card label="Sparks" value={counts.sparks} /><Card label="Pending review" value={counts.pending_review} /><Card label="Approved Charges" value={counts.approved_charges} />
        <Card label="Signals" value={counts.signals} /><Card label="Graph edges" value={counts.graph_edges} /><Card label="Reputation events" value={counts.reputation_events} /><Card label="Regulator proposals" value={counts.regulator_proposals} />
        <Card label="Open proposals" value={counts.open_proposals} /><Card label="Hygiene warnings" value={counts.hygiene_warnings} /><Card label="Grid" value={summary?.grid_status || "empty"} />
      </div>
      <h3>Selected Cell</h3>{raw ? <JsonBlock value={summary || selectedCell} /> : <p>{String(selectedCell?.cell_path || "No Cell selected")}</p>}
      <h3>Ingestion Console</h3>
      <p>Validate adapter config, dry-run discovery, then ingest into the selected Cell.</p>
      <input value={configPath} onChange={(e) => setConfigPath(e.target.value)} placeholder="/path/to/adapter.yaml" />
      <button onClick={async () => { const r = await run(() => api.validate({ config_path: configPath })); if (r) setActionResult(r); }}>Validate config</button>
      <button onClick={async () => { const r = await run(() => api.ingest({ config_path: configPath, cell_path: selectedCell?.cell_path || summary?.cell_path, dry_run: true })); if (r) setActionResult(r); }}>Dry-run discover</button>
      <button onClick={async () => { const r = await run(() => api.ingest({ config_path: configPath, cell_path: selectedCell?.cell_path || summary?.cell_path, dry_run: false })); if (r) { setActionResult(r); refreshSummary(); } }}>Ingest</button>
      {actionResult && <JsonBlock value={actionResult} />}
    </section>}

    {tab === "Review" && <section><h2>Spark Review Queue</h2><button onClick={() => loadTab("Review")}>Load queue</button><div className="actions"><input value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="spark id" /><input value={rationale} onChange={(e) => setRationale(e.target.value)} placeholder="review rationale" /><button onClick={async () => { const r = await run(() => api.reviewSpark(root, cellId, targetId, { action: "approve", rationale })); if (r) { setActionResult(r); loadTab("Review"); } }}>Approve</button><button onClick={async () => { const r = await run(() => api.reviewSpark(root, cellId, targetId, { action: "reject", rationale })); if (r) { setActionResult(r); loadTab("Review"); } }}>Reject</button></div><JsonBlock value={actionResult || rows || "Load queue, enter Spark ID and rationale, then approve or reject. Split/merge are available through the same backend endpoint."} /></section>}

    {tab === "Charges" && <section><h2>Charge Explorer</h2><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="search charges" /><button onClick={() => loadTab("Charges")}>Search</button><div className="actions"><input value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="charge id" /><input value={rationale} onChange={(e) => setRationale(e.target.value)} placeholder="lifecycle reason" /><button onClick={async () => { const r = await run(() => api.chargeAction(root, cellId, targetId, { action: "deprecate", reason: rationale })); if (r) { setActionResult(r); loadTab("Charges"); } }}>Deprecate</button><button onClick={async () => { const r = await run(() => api.chargeAction(root, cellId, targetId, { action: "challenge", reason: rationale })); if (r) { setActionResult(r); loadTab("Charges"); } }}>Challenge</button><button onClick={async () => { const r = await run(() => api.chargeAction(root, cellId, targetId, { action: "forget", reason: rationale })); if (r) { setActionResult(r); loadTab("Charges"); } }}>Forget</button></div><JsonBlock value={actionResult || rows || "Search to inspect provenance, lifecycle state, Signals, and confidence events. Enter a Charge ID to append a lifecycle event."} /></section>}

    {tab === "Packs" && <section><h2>Pack Debugger</h2><textarea value={query} onChange={(e) => setQuery(e.target.value)} /><label>Retrieval mode <select value={retrievalMode} onChange={(e) => setRetrievalMode(e.target.value)}>{["balanced", "conservative", "exploratory", "risk_averse", "audit", "rule_only", "low_latency"].map((mode) => <option key={mode} value={mode}>{mode}</option>)}</select></label><button onClick={async () => { const p = await run(() => api.pack(root, cellId, { query, external_system: "console", external_scope: "debugger", max_items: 10, max_tokens: 2000, retrieval_mode: retrievalMode })); if (p) setPack(p); }}>Generate Pack</button><JsonBlock value={pack || "Generate a Pack to inspect selected items, score trace, risks, retrieval mode, graph context, and token budget."} /></section>}

    {tab === "Signal" && <section><h2>Signal Console</h2><textarea value={JSON.stringify({ loadout_id: (pack?.loadout_id as string) || "", result: "success", external_system: "console", external_scope: "manual", applied_trace_ids: pack?.selected_ids || [], useful_trace_ids: pack?.selected_ids || [], missing_memory_notes: [], verification_evidence: {} }, null, 2)} readOnly /><button onClick={async () => { const s = await run(() => api.signal(root, cellId, { loadout_id: (pack?.loadout_id as string) || "manual", result: "success", external_system: "console", external_scope: "manual", applied_trace_ids: pack?.selected_ids || [], useful_trace_ids: pack?.selected_ids || [], missing_memory_notes: [], verification_evidence: { console: true } })); if (s) setSignal(s); }}>Record Signal</button><JsonBlock value={signal || "Record a Signal after a Pack is used."} /></section>}

    {tab === "Frontier" && <section><h2>Frontier review surfaces</h2><p>Read-only public-safe projections: graph edges, reputation summaries, review-gated regulator proposals, synthetic eval tasks, and dry-run policy simulation.</p><div className="actions"><button onClick={() => loadTab("Frontier")}>Load frontier surfaces</button><label>Current mode <select value={retrievalMode} onChange={(e) => setRetrievalMode(e.target.value)}>{["balanced", "conservative", "exploratory", "risk_averse", "audit", "rule_only", "low_latency"].map((mode) => <option key={mode} value={mode}>{mode}</option>)}</select></label><label>Proposed mode <select value={proposedMode} onChange={(e) => setProposedMode(e.target.value)}>{["balanced", "conservative", "exploratory", "risk_averse", "audit", "rule_only", "low_latency"].map((mode) => <option key={mode} value={mode}>{mode}</option>)}</select></label><button onClick={async () => { const r = await run(() => api.simulate({ cell_path: String(selectedCell?.cell_path || summary?.cell_path || ""), query, task_id: "console-simulation", current_mode: retrievalMode, proposed_mode: proposedMode, max_items: 10, max_tokens: 2000 })); if (r) setSimulation(r); }}>Run read-only simulation</button></div><JsonBlock value={simulation || rows || "Load surfaces or run a simulation. Simulations are read-only and cannot apply policy changes."} /></section>}


    {tab === "Multi-cell" && <section><h2>Multi-cell review surfaces</h2><p>Local-first, explicit cross-cell only. Registry listing is metadata-only; resonance is dry-run/read-only; rules and imports require operator review.</p><label>Registry <input value={registryPath} onChange={(e) => setRegistryPath(e.target.value)} /></label><label>Explicit cell IDs <input value={crossCellIds} onChange={(e) => setCrossCellIds(e.target.value)} placeholder="project-alpha,project-beta" /></label><div className="actions"><button onClick={async () => { const r = await run(() => api.registryCells(registryPath)); if (r) setRows(r); }}>List registered cells</button><button onClick={async () => { const r = await run(() => api.resonanceScan({ registry: registryPath, cell_ids: crossCellIds.split(",").map((s) => s.trim()).filter(Boolean), threshold: 0.25 })); if (r) setRows(r); }}>Dry-run resonance scan</button><button onClick={async () => { const r = await run(() => api.ruleQueue(String(selectedCell?.cell_path || summary?.cell_path || ""))); if (r) setRows(r); }}>Rule review queue</button><button onClick={async () => { const r = await run(() => api.importQueue(String(selectedCell?.cell_path || summary?.cell_path || ""))); if (r) setRows(r); }}>Import review queue</button></div><p>Trust labels: local, imported, federated, verified. Cross-cell scope is active only when explicit cells are provided.</p><JsonBlock value={rows || "Choose a registry and explicit cells to inspect provenance and review queues."} /></section>}

    {tab === "Reports" && <section><h2>Hygiene, Sweep, Proposals, Metrics</h2><button onClick={() => loadTab("Reports")}>Load reports</button>{cellId && <a href={`${apiUrlForCsv(root, cellId)}`}>Export metrics CSV</a>}<div className="actions"><input value={targetId} onChange={(e) => setTargetId(e.target.value)} placeholder="proposal id" /><input value={rationale} onChange={(e) => setRationale(e.target.value)} placeholder="decision rationale" /><button onClick={async () => { const r = await run(() => api.decideProposal(root, cellId, targetId, { decision: "accept", rationale })); if (r) { setActionResult(r); loadTab("Reports"); refreshSummary(); } }}>Accept</button><button onClick={async () => { const r = await run(() => api.decideProposal(root, cellId, targetId, { decision: "reject", rationale })); if (r) { setActionResult(r); loadTab("Reports"); refreshSummary(); } }}>Reject</button><button onClick={async () => { const r = await run(() => api.decideProposal(root, cellId, targetId, { decision: "defer", rationale })); if (r) { setActionResult(r); loadTab("Reports"); refreshSummary(); } }}>Defer</button></div><JsonBlock value={actionResult || rows || "Load reports to inspect memory health, proposals, pilot usefulness, operator burden, and policy tuning. Enter a proposal ID to record an append-only decision."} /></section>}

    {tab === "Settings" && <section><h2>Settings</h2><p>Backend URL is configured by VITE_SHYFTR_API_URL. Cell root is configured by VITE_SHYFTR_CELL_ROOT or sent as a query parameter.</p><JsonBlock value={{ root, cellId, api: "local HTTP service", boundary: "UI projections only; writes delegate to append-only backend endpoints" }} /></section>}
  </main>;
}

function apiUrlForCsv(root: string, cellId: string): string {
  const base = (import.meta.env.VITE_SHYFTR_API_URL || "http://127.0.0.1:8014") as string;
  return `${base}/cell/${encodeURIComponent(cellId)}/metrics.csv?root=${encodeURIComponent(root)}`;
}

createRoot(document.getElementById("root")!).render(<App />);
