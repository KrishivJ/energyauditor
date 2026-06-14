import type { AnalysisConfig, Results } from "../lib/api";
import { inr, kw, kwh, pct, range, tco2 } from "../lib/format";
import LoadProfileChart from "./charts/LoadProfileChart";
import MixBars from "./charts/MixBars";
import Flags from "./Flags";
import Assumptions from "./Assumptions";

function Stat({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: string;
}) {
  return (
    <div className="panel p-4">
      <div className="label">{label}</div>
      <div
        className="mt-1 font-display text-2xl font-semibold"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}

export default function Dashboard({
  results,
  config,
}: {
  results: Results;
  config: AnalysisConfig;
}) {
  const r = results;
  return (
    <div className="space-y-6">
      {/* Headline: unoccupied share */}
      <div className="panel flex flex-col items-start gap-2 p-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="label">
            Energy used while the building is unoccupied
          </div>
          <div className="mt-1 font-display text-5xl font-bold text-waste">
            {pct(r.unoccupiedShare)}
          </div>
          <div className="mt-1 text-sm text-muted">
            {pct(r.unoccupiedWeekdayOffhoursShare)} weekday off-hours ·{" "}
            {pct(r.unoccupiedWeekendShare)} weekends
          </div>
        </div>
        <div className="text-sm text-[#c7d3dc] md:text-right">
          <div className="label">
            Recoverable opportunity (annual, indicative)
          </div>
          <div className="mt-1 font-display text-xl text-save">
            {inr(r.recoverableCostLow)} – {inr(r.recoverableCostHigh)}
          </div>
          <div className="text-xs text-muted">
            {tco2(r.recoverableCarbonLow)} – {tco2(r.recoverableCarbonHigh)}{" "}
            avoided
          </div>
        </div>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat
          label="Total energy (excl. solar)"
          value={kwh(r.totalKwh.mid)}
          sub={`band ${range(r.totalKwh.low, r.totalKwh.high, "kWh")}`}
          accent="#f4b740"
        />
        <Stat
          label="Average load"
          value={kw(r.averageLoadKw)}
          sub={`over ${r.periodDays} days`}
        />
        <Stat
          label="Deep-night baseload"
          value={kw(r.baseloadKw)}
          sub="always-on floor (01–04h)"
          accent="#5b8fc7"
        />
        <Stat label="Peak hourly mean" value={kw(r.peakKw)} />
      </div>

      {/* Profile + mix */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="panel p-5 lg:col-span-2">
          <h3 className="font-display font-semibold">Daily load profile</h3>
          <p className="text-xs text-muted">
            Mean building load by hour — working days vs off days. Shaded band
            is the assumed occupied window.
          </p>
          <div className="mt-3">
            <LoadProfileChart
              working={r.hourlyProfile.workingDays}
              off={r.hourlyProfile.offDays}
              occupiedStart={config.occupiedStartHour}
              occupiedEnd={config.occupiedEndHour}
            />
          </div>
        </div>
        <div className="panel p-5">
          <h3 className="font-display font-semibold">Load mix by type</h3>
          <p className="mb-3 text-xs text-muted">
            Share of total (mid power factor).
          </p>
          <MixBars mix={r.loadMix} />
        </div>
      </div>

      {/* Cost / carbon */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat
          label="Period cost"
          value={inr(r.periodCost.mid)}
          sub={`${inr(r.periodCost.low)} – ${inr(r.periodCost.high)}`}
        />
        <Stat
          label="Annualised cost (indicative)"
          value={inr(r.annualCost.mid)}
          sub="extrapolated from window"
        />
        <Stat
          label="Period carbon"
          value={tco2(r.periodCarbonTco2)}
          accent="#57b894"
        />
        <Stat
          label="Annual carbon (indicative)"
          value={tco2(r.annualCarbonTco2)}
          sub="extrapolated from window"
        />
      </div>

      {/* Flags + assumptions */}
      <div className="grid gap-6 lg:grid-cols-2">
        <Flags flags={r.flags} />
        <Assumptions results={r} />
      </div>

      {/* Solar (reported separately) */}
      {r.solar.length > 0 && (
        <div className="panel p-5">
          <h3 className="font-display font-semibold">
            Solar — reported separately, excluded from totals
          </h3>
          <ul className="mt-2 space-y-1 text-sm text-[#c7d3dc]">
            {r.solar.map((s) => (
              <li key={s.filename} className="flex justify-between">
                <span>{s.circuitName}</span>
                <span className="text-muted">{kwh(s.kwh.mid)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
