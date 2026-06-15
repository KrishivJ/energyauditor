import { useEffect, useState } from "react";
import type { LoadMixEntry } from "../../lib/api";
import { LOAD_TYPE_COLOR } from "../../lib/api";
import { pct, kwh } from "../../lib/format";

// Horizontal load-mix bars. Bars grow from zero on mount; hovering a row lifts
// it and dims the rest so a single category is easy to read.
export default function MixBars({ mix }: { mix: LoadMixEntry[] }) {
  const maxShare = Math.max(0.0001, ...mix.map((m) => m.share));
  const [grown, setGrown] = useState(false);
  const [hover, setHover] = useState<string | null>(null);

  useEffect(() => {
    const t = requestAnimationFrame(() => setGrown(true));
    return () => cancelAnimationFrame(t);
  }, []);

  return (
    <div className="space-y-3">
      {mix.map((m, i) => {
        const dim = hover !== null && hover !== m.loadType;
        return (
          <div
            key={m.loadType}
            onMouseEnter={() => setHover(m.loadType)}
            onMouseLeave={() => setHover(null)}
            className="cursor-default transition-opacity duration-200"
            style={{ opacity: dim ? 0.45 : 1 }}
          >
            <div className="mb-1 flex justify-between text-sm">
              <span>{m.loadType}</span>
              <span className="text-muted tabular-nums">
                {pct(m.share, 1)} · {kwh(m.kwh)}
              </span>
            </div>
            <div className="h-2.5 w-full rounded bg-ink">
              <div
                className="h-2.5 rounded transition-[width] duration-700 ease-out"
                style={{
                  width: grown ? `${(m.share / maxShare) * 100}%` : "0%",
                  transitionDelay: `${i * 70}ms`,
                  background: LOAD_TYPE_COLOR[m.loadType] ?? "#f4b740",
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
