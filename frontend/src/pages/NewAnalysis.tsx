import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Uploader from "../components/Uploader";
import MappingPanel from "../components/MappingPanel";
import ConfigPanel from "../components/ConfigPanel";
import { api, defaultConfig } from "../lib/api";
import type { AnalysisConfig, FileMeta } from "../lib/api";

export default function NewAnalysis() {
  const nav = useNavigate();
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [files, setFiles] = useState<FileMeta[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [config, setConfig] = useState<AnalysisConfig>(defaultConfig());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = async (picked: File[]) => {
    setBusy(true);
    setError(null);
    try {
      const res = await api.upload(picked);
      setAnalysisId(res.analysisId);
      setFiles(res.files);
      setWarnings(res.warnings);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const run = async () => {
    if (!analysisId) return;
    setBusy(true);
    setError(null);
    try {
      await api.setConfig(analysisId, config);
      await api.run(analysisId);
      nav(`/analysis/${analysisId}`);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="font-display text-2xl font-semibold">New analysis</h1>

      {error && (
        <div className="panel border-waste/50 bg-waste/10 p-4 text-sm text-waste">
          {error}
        </div>
      )}

      {!analysisId ? (
        <Uploader onFiles={upload} busy={busy} />
      ) : (
        <>
          {warnings.length > 0 && (
            <div className="panel border-amber/40 bg-amber/5 p-4 text-sm">
              <div className="label mb-1 text-amber">Parse notes</div>
              <ul className="list-disc space-y-0.5 pl-5 text-[#c7d3dc]">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              <MappingPanel
                files={files}
                config={config}
                onChange={setConfig}
              />
            </div>
            <ConfigPanel config={config} onChange={setConfig} />
          </div>
          <div className="flex items-center gap-3">
            <button className="btn btn-primary" disabled={busy} onClick={run}>
              {busy ? "Running…" : "Run analysis"}
            </button>
            <span className="text-sm text-muted">
              {files.length} circuit(s) ready.
            </span>
          </div>
        </>
      )}
    </div>
  );
}
