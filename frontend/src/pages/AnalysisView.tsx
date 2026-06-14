import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Dashboard from "../components/Dashboard";
import MappingPanel from "../components/MappingPanel";
import ConfigPanel from "../components/ConfigPanel";
import { api, defaultConfig } from "../lib/api";
import type { AnalysisDetail, AnalysisConfig } from "../lib/api";
import { fmtDate } from "../lib/format";

export default function AnalysisView() {
  const { id } = useParams<{ id: string }>();
  const nav = useNavigate();
  const [detail, setDetail] = useState<AnalysisDetail | null>(null);
  const [config, setConfig] = useState<AnalysisConfig>(defaultConfig());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    if (!id) return;
    api
      .get(id)
      .then((d) => {
        setDetail(d);
        if (d.config) setConfig(d.config);
      })
      .catch((e) => setError((e as Error).message));
  };

  useEffect(load, [id]);

  const rerun = async () => {
    if (!id) return;
    setBusy(true);
    setError(null);
    try {
      await api.setConfig(id, config);
      await api.run(id);
      load();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!id || !confirm("Delete this analysis?")) return;
    await api.remove(id);
    nav("/");
  };

  if (error)
    return (
      <div className="panel border-waste/50 bg-waste/10 p-4 text-sm text-waste">
        {error}
      </div>
    );
  if (!detail) return <div className="text-sm text-muted">Loading…</div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-semibold">{detail.name}</h1>
          <div className="text-xs text-muted">
            {fmtDate(detail.createdAt)} · {detail.files.length} circuits ·{" "}
            <span className="uppercase">{detail.status}</span>
          </div>
        </div>
        <div className="flex gap-2">
          <button className="btn" disabled={busy} onClick={rerun}>
            {busy ? "Running…" : "Re-run"}
          </button>
          <button className="btn" onClick={remove}>
            Delete
          </button>
        </div>
      </div>

      {detail.results ? (
        <Dashboard results={detail.results} config={config} />
      ) : (
        <>
          <div className="panel border-amber/40 bg-amber/5 p-4 text-sm text-[#c7d3dc]">
            This analysis hasn't been run yet. Review the mapping and
            assumptions, then run it.
          </div>
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <MappingPanel
                files={detail.files}
                config={config}
                onChange={setConfig}
              />
            </div>
            <ConfigPanel config={config} onChange={setConfig} />
          </div>
          <button className="btn btn-primary" disabled={busy} onClick={rerun}>
            {busy ? "Running…" : "Run analysis"}
          </button>
        </>
      )}
    </div>
  );
}
