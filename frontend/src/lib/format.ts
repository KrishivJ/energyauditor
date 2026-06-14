// Display helpers. Reports ranges and rounded figures — never false precision.

export const pct = (x: number, dp = 0) => `${(x * 100).toFixed(dp)}%`;

export const kwh = (x: number) => `${Math.round(x).toLocaleString()} kWh`;

export const kw = (x: number) => `${Math.round(x).toLocaleString()} kW`;

export const range = (low: number, high: number, unit = "") =>
  `${Math.round(low).toLocaleString()}–${Math.round(high).toLocaleString()}${unit ? " " + unit : ""}`;

// INR with lakh/crore phrasing for senior-management readability.
export function inr(x: number): string {
  if (x >= 1e7) return `₹${(x / 1e7).toFixed(2)} crore`;
  if (x >= 1e5) return `₹${(x / 1e5).toFixed(2)} lakh`;
  return `₹${Math.round(x).toLocaleString("en-IN")}`;
}

export const tco2 = (x: number) => `${x.toFixed(1)} tCO₂`;

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
