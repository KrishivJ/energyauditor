import type { Results } from "../lib/api";
import { inr, pct, tco2 } from "../lib/format";
import { AnimatedNumber, Stat } from "./Stat";
import Recommendations from "./Recommendations";

// The "verdict" tab: what the data means and what to do — the headline waste
// figure, the money/carbon at stake, and prioritised actions.
export default function ResultsTab({ results: r }: { results: Results }) {
  return (
    <div className="space-y-6">
      {/* Headline: unoccupied share + recoverable opportunity */}
      <div className="panel anim-fade-up flex flex-col items-start gap-2 p-6 md:flex-row md:items-end md:justify-between">
        <div>
          <div className="label">
            Energy used while the building is unoccupied
          </div>
          <div className="mt-1 font-display text-5xl font-bold tabular-nums text-waste">
            <AnimatedNumber value={r.unoccupiedShare} format={(n) => pct(n)} />
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

      {/* Cost / carbon */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Stat
          index={0}
          label="Period cost"
          value={<AnimatedNumber value={r.periodCost.mid} format={inr} />}
          sub={`${inr(r.periodCost.low)} – ${inr(r.periodCost.high)}`}
        />
        <Stat
          index={1}
          label="Annualised cost (indicative)"
          value={<AnimatedNumber value={r.annualCost.mid} format={inr} />}
          sub="extrapolated from window"
        />
        <Stat
          index={2}
          label="Period carbon"
          value={<AnimatedNumber value={r.periodCarbonTco2} format={tco2} />}
          accent="#57b894"
        />
        <Stat
          index={3}
          label="Annual carbon (indicative)"
          value={<AnimatedNumber value={r.annualCarbonTco2} format={tco2} />}
          sub="extrapolated from window"
        />
      </div>

      {/* Recommendations — what to do about the numbers above */}
      <Recommendations results={r} />
    </div>
  );
}
