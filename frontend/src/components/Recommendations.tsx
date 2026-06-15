// Derives prioritised, data-grounded efficiency actions from the engine results.
// Pure UI: every recommendation cites real figures from this analysis (no
// generic advice, no fabricated numbers) so the user can trust and act on it.

import type { Results } from "../lib/api";
import { inr, kw, pct } from "../lib/format";

type Priority = "high" | "medium" | "low";

type Rec = {
  id: string;
  priority: Priority;
  title: string;
  body: string;
  impact?: string; // indicative ₹/year or data-quality note
};

const PRIORITY_RANK: Record<Priority, number> = { high: 0, medium: 1, low: 2 };

const PRIORITY_STYLE: Record<Priority, { color: string; label: string }> = {
  high: { color: "#e8743b", label: "High impact" },
  medium: { color: "#f4b740", label: "Worth doing" },
  low: { color: "#5b8fc7", label: "Housekeeping" },
};

function shareOf(r: Results, type: string): number {
  const e = r.loadMix.find((m) => m.loadType === type);
  return e ? e.share : 0;
}

// Build the recommendation list from thresholds on the analysis outputs. Each
// rule only fires when the data warrants it, so an efficient building shows few.
function buildRecommendations(r: Results): Rec[] {
  const recs: Rec[] = [];
  const recoverable = `${inr(r.recoverableCostLow)} – ${inr(r.recoverableCostHigh)}/yr`;

  // 1. Unoccupied energy — the headline opportunity.
  if (r.unoccupiedShare >= 0.1) {
    const weekendHeavy = r.unoccupiedWeekendShare >= r.unoccupiedWeekdayOffhoursShare;
    recs.push({
      id: "unoccupied",
      priority: r.unoccupiedShare >= 0.25 ? "high" : "medium",
      title: `Cut energy used while the building is empty (${pct(r.unoccupiedShare)} of total)`,
      body: weekendHeavy
        ? `Weekends are the biggest leak (${pct(r.unoccupiedWeekendShare)} of total energy). Add a 7-day time schedule to HVAC, lighting and general-power circuits so they default OFF on non-working days, and require a manual override for weekend occupancy.`
        : `Most waste is weekday after-hours (${pct(r.unoccupiedWeekdayOffhoursShare)} of total). Set the BMS / time-clocks to ramp plant down at the end of the occupied window and verify nothing restarts unattended overnight.`,
      impact: `Recoverable ${recoverable}`,
    });
  }

  // 2. Always-on floor — high deep-night baseload relative to the daily average.
  const baseloadRatio = r.averageLoadKw > 0 ? r.baseloadKw / r.averageLoadKw : 0;
  if (baseloadRatio >= 0.4 && r.baseloadKw > 0) {
    recs.push({
      id: "baseload",
      priority: baseloadRatio >= 0.6 ? "high" : "medium",
      title: `Trim the always-on floor (${kw(r.baseloadKw)} runs at 01–04h)`,
      body: `Deep-night load is ${pct(baseloadRatio)} of your daily average — high for an unoccupied building. Walk the site after hours to find what stays on: idle AHUs/pumps, standby UPS losses, vending, signage, IT and phantom loads. Each kW removed here saves around the clock.`,
    });
  }

  // 3. HVAC dominance — biggest single lever in most Indian commercial buildings.
  const hvac = shareOf(r, "HVAC");
  if (hvac >= 0.35) {
    recs.push({
      id: "hvac",
      priority: hvac >= 0.5 ? "high" : "medium",
      title: `Optimise HVAC (${pct(hvac)} of building load)`,
      body: `Cooling is your largest end use. Raise chilled-water / thermostat setpoints by 1–2 °C, tighten the occupied schedule to match real hours, enable economiser / free-cooling where ambient allows, and service filters and coils. A 1 °C setpoint change is typically 3–5% of HVAC energy.`,
    });
  }

  // 4. Lighting — strong candidate for retrofit + controls.
  const lighting = shareOf(r, "Lighting");
  if (lighting >= 0.12) {
    recs.push({
      id: "lighting",
      priority: "medium",
      title: `Address lighting (${pct(lighting)} of building load)`,
      body: `Convert any remaining conventional fittings to LED and add occupancy sensors and daylight-linked dimming in low-traffic zones (corridors, washrooms, car parks, store rooms). These pay back quickly and also cut off-hours waste.`,
    });
  }

  // 5. Peak demand — load factor signals demand-charge exposure.
  const peakRatio = r.averageLoadKw > 0 ? r.peakKw / r.averageLoadKw : 0;
  if (peakRatio >= 2 && r.peakKw > 0) {
    recs.push({
      id: "peak",
      priority: "medium",
      title: `Flatten the demand peak (peak ${kw(r.peakKw)} vs ${kw(r.averageLoadKw)} average)`,
      body: `Your peak is ${peakRatio.toFixed(1)}× the average load, so a poor load factor is likely inflating maximum-demand charges. Stagger large equipment start-ups, pre-cool before the peak window, and review the sanctioned demand against your actual profile with your DISCOM tariff.`,
    });
  }

  // 6. Metering quality — substituted voltage channels weaken the numbers.
  const badMeters = r.circuits.filter((c) => c.voltageSubstituted);
  if (badMeters.length > 0) {
    recs.push({
      id: "metering",
      priority: "low",
      title: `Fix ${badMeters.length} meter${badMeters.length > 1 ? "s" : ""} with a faulty voltage channel`,
      body: `These circuits logged an implausibly low voltage and were corrected with the building-wide healthy median, which widens the uncertainty on their energy: ${badMeters
        .map((c) => c.circuitName)
        .join(", ")}. Re-terminate the VT/PT wiring or replace the channel so future readings need no substitution.`,
      impact: "Improves accuracy, not energy",
    });
  }

  // 7. Solar — encourage where there's a clear daytime cooling load and none yet.
  if (r.solar.length === 0 && hvac >= 0.3) {
    recs.push({
      id: "solar",
      priority: "low",
      title: "Evaluate rooftop solar",
      body: "Your load is daytime- and cooling-led, which lines up well with a solar generation curve. A feasibility study on available roof area could offset a meaningful share of daytime consumption and the HVAC peak.",
    });
  }

  return recs.sort((a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]);
}

function RecCard({ rec }: { rec: Rec }) {
  const style = PRIORITY_STYLE[rec.priority];
  return (
    <div className="panel border-l-2 p-4" style={{ borderLeftColor: style.color }}>
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-display font-semibold leading-snug">{rec.title}</h4>
        <span
          className="shrink-0 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider"
          style={{ color: style.color, borderColor: `${style.color}66` }}
        >
          {style.label}
        </span>
      </div>
      <p className="mt-2 text-sm text-[#c7d3dc]">{rec.body}</p>
      {rec.impact && (
        <div className="mt-2 text-xs font-medium text-save">{rec.impact}</div>
      )}
    </div>
  );
}

export default function Recommendations({ results }: { results: Results }) {
  const recs = buildRecommendations(results);

  return (
    <div className="panel p-5">
      <h3 className="font-display font-semibold">Recommended actions</h3>
      <p className="text-xs text-muted">
        Prioritised from this analysis. Savings figures are indicative ranges —
        confirm against a detailed audit and your electricity bill.
      </p>
      <div className="mt-4 space-y-3">
        {recs.length === 0 ? (
          <p className="text-sm text-[#c7d3dc]">
            No major inefficiencies stood out in this dataset — unoccupied waste,
            baseload and load mix are all within healthy ranges. Keep monitoring
            to catch drift.
          </p>
        ) : (
          recs.map((rec) => <RecCard key={rec.id} rec={rec} />)
        )}
      </div>
    </div>
  );
}
