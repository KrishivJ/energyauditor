import type { Results } from "../lib/api";

type AssumptionShape = {
  mode?: string;
  occupied_hours?: number[];
  working_days?: string[];
  interval_hours?: number;
  baseload_window?: number[];
  power_factor_bands?: string;
  tariff?: {
    low?: number;
    mid?: number;
    high?: number;
    currency?: string;
    unit?: string;
    note?: string;
  };
  emission_factor_tco2_per_mwh?: number;
  recoverable_fraction?: number[];
  annualisation?: string;
};

// Echoes every changeable input the figures depend on (brief §8).
export default function Assumptions({ results }: { results: Results }) {
  const a = results.assumptions as AssumptionShape;
  const rows: Array<[string, string]> = [
    ["Meter mode", String(a.mode)],
    [
      "Occupied hours",
      `${a.occupied_hours?.[0]}:00 – ${a.occupied_hours?.[1]}:00`,
    ],
    ["Working days", (a.working_days ?? []).join(", ")],
    ["Reading interval", `${a.interval_hours} h`],
    [
      "Baseload window",
      `${a.baseload_window?.[0]}:00 – ${a.baseload_window?.[1]}:00`,
    ],
    ["Power factor", String(a.power_factor_bands)],
    [
      "Tariff",
      `${a.tariff?.low}/${a.tariff?.mid}/${a.tariff?.high} ${a.tariff?.currency} ${a.tariff?.unit}`,
    ],
    ["Emission factor", `${a.emission_factor_tco2_per_mwh} tCO₂/MWh`],
    [
      "Recoverable fraction",
      `${a.recoverable_fraction?.[0]}–${a.recoverable_fraction?.[1]}`,
    ],
  ];
  return (
    <div className="panel p-5">
      <h3 className="font-display font-semibold">Assumptions</h3>
      <dl className="mt-3 space-y-1.5 text-sm">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-4">
            <dt className="text-muted">{k}</dt>
            <dd className="text-right text-[#c7d3dc]">{v}</dd>
          </div>
        ))}
      </dl>
      <p className="mt-3 text-xs text-amber/80">{a.tariff?.note}</p>
      <p className="mt-1 text-xs text-muted">{a.annualisation}</p>
    </div>
  );
}
