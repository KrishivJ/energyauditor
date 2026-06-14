import type { AnalysisConfig, ColumnOverride, FileMeta } from "../lib/api";
import { LOAD_TYPE_COLOR } from "../lib/api";

// Per-file detected column mapping with manual override (brief §2, §4).
// Detection runs per file, so the voltage column may sit at a different index
// in files that log frequency — this panel surfaces that transparently.

const COLS: Array<{ key: keyof ColumnOverride; label: string }> = [
  { key: "headerRow", label: "Header row" },
  { key: "timestamp", label: "Timestamp" },
  { key: "value", label: "Value (current/energy)" },
  { key: "voltage", label: "Voltage (LL)" },
];

export default function MappingPanel({
  files,
  config,
  onChange,
}: {
  files: FileMeta[];
  config: AnalysisConfig;
  onChange: (c: AnalysisConfig) => void;
}) {
  const setOverride = (
    filename: string,
    key: keyof ColumnOverride,
    raw: string,
  ) => {
    const next = { ...config.columnOverrides };
    const ov: ColumnOverride = { ...next[filename] };
    ov[key] = raw === "" ? null : Number(raw);
    next[filename] = ov;
    onChange({ ...config, columnOverrides: next });
  };

  const effective = (f: FileMeta, key: keyof ColumnOverride): number | null => {
    const ov = config.columnOverrides[f.filename]?.[key];
    if (ov !== undefined && ov !== null) return ov;
    if (key === "headerRow") return f.headerRow;
    return f.detectedCols[key as string] ?? null;
  };

  return (
    <div className="panel p-6">
      <h2 className="font-display text-lg font-semibold">
        Circuits &amp; column mapping
      </h2>
      <p className="mt-1 text-sm text-muted">
        Detected per file. Override any column if a meter is laid out
        differently (leave blank to use detection).
      </p>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-muted">
              <th className="py-2 pr-3">Circuit</th>
              <th className="px-2">Type</th>
              <th className="px-2">Rows</th>
              {COLS.map((c) => (
                <th key={c.key} className="px-2">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {files.map((f) => {
              const missing =
                config.mode === "cv"
                  ? f.detectedCols.value == null ||
                    f.detectedCols.voltage == null
                  : f.detectedCols.value == null;
              return (
                <tr key={f.filename} className="border-b border-hairline/60">
                  <td className="py-2 pr-3">
                    <div className="font-medium">{f.circuitName}</div>
                    <div className="text-xs text-muted">{f.filename}</div>
                    {f.warnings.length > 0 && (
                      <div className="mt-0.5 text-xs text-waste">
                        {f.warnings.join(" ")}
                      </div>
                    )}
                  </td>
                  <td className="px-2">
                    <span
                      className="rounded px-1.5 py-0.5 text-xs"
                      style={{
                        color: LOAD_TYPE_COLOR[f.loadType] ?? "#fff",
                        background: `${LOAD_TYPE_COLOR[f.loadType] ?? "#fff"}1a`,
                      }}
                    >
                      {f.loadType}
                    </span>
                  </td>
                  <td
                    className={`px-2 ${f.rowCount === 0 ? "text-waste" : ""}`}
                  >
                    {f.rowCount.toLocaleString()}
                  </td>
                  {COLS.map((c) => {
                    const disabled =
                      c.key === "voltage" && config.mode === "energy";
                    return (
                      <td key={c.key} className="px-2">
                        <input
                          type="number"
                          className="input w-20"
                          disabled={disabled}
                          placeholder={
                            effective(f, c.key) == null
                              ? "—"
                              : String(effective(f, c.key))
                          }
                          value={
                            config.columnOverrides[f.filename]?.[c.key] ?? ""
                          }
                          onChange={(e) =>
                            setOverride(f.filename, c.key, e.target.value)
                          }
                        />
                      </td>
                    );
                  })}
                  {missing && (
                    <td className="px-2 text-xs text-waste">needs mapping</td>
                  )}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-3 text-xs text-muted">
        Column indices are 0-based. Header row is the row containing column
        labels (data starts on the next row).
      </p>
    </div>
  );
}
