// Data-quality flags from the engine (brief §8): faulty-voltage substitutions,
// solar exclusion, gaps, coverage. Surfaced, never hidden.

const ICON: Record<string, string> = {
  faulty_voltage_substituted: "⚡",
  solar_excluded: "☀",
  timestamp_gaps: "⏱",
  coverage: "✓",
};

const TONE: Record<string, string> = {
  faulty_voltage_substituted: "text-waste",
  solar_excluded: "text-amber",
  timestamp_gaps: "text-waste",
  coverage: "text-save",
};

export default function Flags({
  flags,
}: {
  flags: Array<Record<string, unknown>>;
}) {
  return (
    <div className="panel p-5">
      <h3 className="font-display font-semibold">Data quality</h3>
      <ul className="mt-3 space-y-2 text-sm">
        {flags.map((f, i) => {
          const type = String(f.type);
          return (
            <li key={i} className="flex gap-2">
              <span className={TONE[type] ?? "text-muted"}>
                {ICON[type] ?? "•"}
              </span>
              <span className="text-[#c7d3dc]">
                {String(f.message ?? type)}
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
