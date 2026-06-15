import type { AnalysisConfig, Results } from "../lib/api";
import { kw, kwh, range } from "../lib/format";
import { AnimatedNumber, Stat } from "./Stat";
import LoadProfileChart from "./charts/LoadProfileChart";
import MixBars from "./charts/MixBars";
import CircuitTable from "./CircuitTable";
import Flags from "./Flags";
import Assumptions from "./Assumptions";

// The "data" tab: how the building actually behaves — measured load, mix,
// per-circuit detail, and the data-quality / assumptions that frame it.
export default function AnalyticsTab({
  results: r,
  config,
}: {
  results: Results;
  config: AnalysisConfig;
}) {
  return (
    <div className="space-y-6">
      {/* Measured stats */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat
          index={0}
          label="Total energy (excl. solar)"
          value={<AnimatedNumber value={r.totalKwh.mid} format={kwh} />}
          sub={`band ${range(r.totalKwh.low, r.totalKwh.high, "kWh")}`}
          accent="#f4b740"
        />
        <Stat
          index={1}
          label="Average load"
          value={<AnimatedNumber value={r.averageLoadKw} format={kw} />}
          sub={`over ${r.periodDays} days`}
        />
        <Stat
          index={2}
          label="Deep-night baseload"
          value={<AnimatedNumber value={r.baseloadKw} format={kw} />}
          sub="always-on floor (01–04h)"
          accent="#5b8fc7"
        />
        <Stat
          index={3}
          label="Peak hourly mean"
          value={<AnimatedNumber value={r.peakKw} format={kw} />}
        />
      </div>

      {/* Profile + mix */}
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="panel anim-fade-up p-5 lg:col-span-2">
          <h3 className="font-display font-semibold">Daily load profile</h3>
          <p className="text-xs text-muted">
            Mean building load by hour — working days vs off days. Hover for
            values; the shaded band is the assumed occupied window.
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
        <div className="panel anim-fade-up p-5" style={{ animationDelay: "80ms" }}>
          <h3 className="font-display font-semibold">Load mix by type</h3>
          <p className="mb-3 text-xs text-muted">
            Share of total (mid power factor). Hover to isolate.
          </p>
          <MixBars mix={r.loadMix} />
        </div>
      </div>

      {/* Per-circuit detail */}
      <CircuitTable circuits={r.circuits} totalMid={r.totalKwh.mid} />

      {/* Data quality + assumptions */}
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
