import type { LoadMixEntry } from "../../lib/api";
import { LOAD_TYPE_COLOR } from "../../lib/api";
import { pct, kwh } from "../../lib/format";

// Horizontal load-mix bars (recharts is fine here, but a simple flex bar reads
// cleaner for a handful of categories and avoids tooltip noise).
export default function MixBars({ mix }: { mix: LoadMixEntry[] }) {
  const maxShare = Math.max(0.0001, ...mix.map((m) => m.share));
  return (
    <div className="space-y-3">
      {mix.map((m) => (
        <div key={m.loadType}>
          <div className="mb-1 flex justify-between text-sm">
            <span>{m.loadType}</span>
            <span className="text-muted">
              {pct(m.share, 1)} · {kwh(m.kwh)}
            </span>
          </div>
          <div className="h-2.5 w-full rounded bg-ink">
            <div
              className="h-2.5 rounded"
              style={{
                width: `${(m.share / maxShare) * 100}%`,
                background: LOAD_TYPE_COLOR[m.loadType] ?? "#f4b740",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
