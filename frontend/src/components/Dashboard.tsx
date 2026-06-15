import { useState } from "react";
import type { AnalysisConfig, Results } from "../lib/api";
import Tabs from "./Tabs";
import AnalyticsTab from "./AnalyticsTab";
import ResultsTab from "./ResultsTab";

const TABS = [
  { id: "results", label: "Results" },
  { id: "analytics", label: "Analytics" },
];

// Tab shell: Results (the verdict — waste, money, actions) and Analytics (the
// measured data — load profile, mix, per-circuit detail). Re-keying the content
// on the active tab replays its entrance animation on switch.
export default function Dashboard({
  results,
  config,
}: {
  results: Results;
  config: AnalysisConfig;
}) {
  const [tab, setTab] = useState("results");

  return (
    <div className="space-y-6">
      <Tabs tabs={TABS} active={tab} onChange={setTab} />
      <div key={tab} className="anim-fade-in">
        {tab === "results" ? (
          <ResultsTab results={results} />
        ) : (
          <AnalyticsTab results={results} config={config} />
        )}
      </div>
    </div>
  );
}
