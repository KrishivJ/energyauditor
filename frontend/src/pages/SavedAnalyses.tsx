import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import type { AnalysisSummary } from "../lib/api";
import { fmtDate } from "../lib/format";

const STATUS_TONE: Record<string, string> = {
  complete: "text-save",
  configured: "text-amber",
  uploaded: "text-muted",
  error: "text-waste",
};

export default function SavedAnalyses() {
  const [items, setItems] = useState<AnalysisSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () =>
    api
      .list()
      .then(setItems)
      .catch((e) => setError((e as Error).message));

  useEffect(() => {
    load();
  }, []);

  const remove = async (id: string) => {
    if (!confirm("Delete this analysis? This cannot be undone.")) return;
    await api.remove(id);
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="font-display text-2xl font-semibold">Saved analyses</h1>
        <Link to="/new" className="btn btn-primary">
          New analysis
        </Link>
      </div>

      {error && (
        <div className="panel border-waste/50 bg-waste/10 p-4 text-sm text-waste">
          {error}
        </div>
      )}

      {items === null ? (
        <div className="text-sm text-muted">Loading…</div>
      ) : items.length === 0 ? (
        <div className="panel p-10 text-center">
          <p className="text-muted">No analyses yet.</p>
          <Link to="/new" className="btn btn-primary mt-4 inline-block">
            Upload meter files
          </Link>
        </div>
      ) : (
        <div className="panel divide-y divide-hairline">
          {items.map((a) => (
            <div key={a.id} className="flex items-center justify-between p-4">
              <div>
                <Link
                  to={`/analysis/${a.id}`}
                  className="font-medium hover:text-amber"
                >
                  {a.name}
                </Link>
                <div className="text-xs text-muted">{fmtDate(a.createdAt)}</div>
              </div>
              <div className="flex items-center gap-4">
                <span
                  className={`text-xs uppercase ${STATUS_TONE[a.status] ?? ""}`}
                >
                  {a.status}
                </span>
                <Link
                  to={`/analysis/${a.id}`}
                  className="btn px-3 py-1 text-xs"
                >
                  Open
                </Link>
                <button
                  className="text-xs text-muted hover:text-waste"
                  onClick={() => remove(a.id)}
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
