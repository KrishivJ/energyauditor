import { useMemo, useState } from "react";
import type { CircuitResult } from "../lib/api";
import { LOAD_TYPE_COLOR } from "../lib/api";
import { kwh, pct } from "../lib/format";

type SortKey = "circuitName" | "loadType" | "kwh" | "medianVoltage";
type Dir = "asc" | "desc";

// Sortable per-circuit breakdown with inline share bars. Surfaces the
// circuit-level detail the engine computes (previously unshown).
export default function CircuitTable({
  circuits,
  totalMid,
}: {
  circuits: CircuitResult[];
  totalMid: number;
}) {
  const [sort, setSort] = useState<{ key: SortKey; dir: Dir }>({
    key: "kwh",
    dir: "desc",
  });

  const sorted = useMemo(() => {
    const arr = [...circuits];
    arr.sort((a, b) => {
      let d = 0;
      switch (sort.key) {
        case "circuitName":
          d = a.circuitName.localeCompare(b.circuitName);
          break;
        case "loadType":
          d = a.loadType.localeCompare(b.loadType);
          break;
        case "kwh":
          d = a.kwh.mid - b.kwh.mid;
          break;
        case "medianVoltage":
          d = a.medianVoltage - b.medianVoltage;
          break;
      }
      return sort.dir === "asc" ? d : -d;
    });
    return arr;
  }, [circuits, sort]);

  const maxKwh = Math.max(0.0001, ...circuits.map((c) => c.kwh.mid));

  const toggle = (key: SortKey) =>
    setSort((s) =>
      s.key === key
        ? { key, dir: s.dir === "asc" ? "desc" : "asc" }
        : { key, dir: key === "circuitName" || key === "loadType" ? "asc" : "desc" },
    );

  const arrow = (key: SortKey) =>
    sort.key === key ? (sort.dir === "asc" ? " ↑" : " ↓") : "";

  const Th = ({
    k,
    children,
    right,
  }: {
    k: SortKey;
    children: React.ReactNode;
    right?: boolean;
  }) => (
    <th
      onClick={() => toggle(k)}
      className={`cursor-pointer select-none pb-2 font-medium text-muted transition-colors hover:text-[#c7d3dc] ${
        right ? "text-right" : "text-left"
      }`}
    >
      {children}
      <span className="text-amber">{arrow(k)}</span>
    </th>
  );

  return (
    <div className="panel p-5">
      <h3 className="font-display font-semibold">Per-circuit breakdown</h3>
      <p className="text-xs text-muted">
        {circuits.length} circuits in building totals. Click a column to sort.
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-xs uppercase tracking-wider">
              <Th k="circuitName">Circuit</Th>
              <Th k="loadType">Type</Th>
              <Th k="kwh" right>
                Energy (kWh)
              </Th>
              <th className="pb-2 text-left font-medium text-muted">Share</th>
              <Th k="medianVoltage" right>
                Median V
              </Th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((c, i) => {
              const color = LOAD_TYPE_COLOR[c.loadType] ?? "#f4b740";
              const share = totalMid > 0 ? c.kwh.mid / totalMid : 0;
              return (
                <tr
                  key={c.filename}
                  className="anim-fade-up border-b border-hairline/50 transition-colors hover:bg-white/[0.02]"
                  style={{ animationDelay: `${Math.min(i, 12) * 35}ms` }}
                >
                  <td className="py-2 pr-3">
                    <div className="flex items-center gap-2">
                      <span
                        className="h-2 w-2 shrink-0 rounded-full"
                        style={{ background: color }}
                      />
                      <span className="text-[#e6edf3]">{c.circuitName}</span>
                      {c.voltageSubstituted && (
                        <span
                          className="rounded border border-waste/40 px-1 text-[10px] text-waste"
                          title="Faulty voltage channel — substituted with the healthy median"
                        >
                          V fixed
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-2 pr-3 text-muted">{c.loadType}</td>
                  <td className="py-2 pr-3 text-right tabular-nums text-[#c7d3dc]">
                    {kwh(c.kwh.mid)}
                  </td>
                  <td className="w-[28%] py-2 pr-3">
                    <div className="flex items-center gap-2">
                      <div className="h-1.5 flex-1 rounded bg-ink">
                        <div
                          className="h-1.5 rounded"
                          style={{
                            width: `${(c.kwh.mid / maxKwh) * 100}%`,
                            background: color,
                          }}
                        />
                      </div>
                      <span className="w-10 shrink-0 text-right text-xs tabular-nums text-muted">
                        {pct(share, 0)}
                      </span>
                    </div>
                  </td>
                  <td className="py-2 text-right tabular-nums text-muted">
                    {Math.round(c.medianVoltage)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
