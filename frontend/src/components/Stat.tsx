import type { ReactNode } from "react";
import { useCountUp } from "../lib/anim";

// Counts a number up on mount, then formats it. Use for headline figures.
export function AnimatedNumber({
  value,
  format,
  duration,
}: {
  value: number;
  format: (n: number) => string;
  duration?: number;
}) {
  const v = useCountUp(value, duration);
  return <>{format(v)}</>;
}

// A single stat tile. `index` staggers its entrance so a grid cascades in.
export function Stat({
  label,
  value,
  sub,
  accent,
  index = 0,
}: {
  label: string;
  value: ReactNode;
  sub?: ReactNode;
  accent?: string;
  index?: number;
}) {
  return (
    <div
      className="panel anim-fade-up p-4"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="label">{label}</div>
      <div
        className="mt-1 font-display text-2xl font-semibold tabular-nums"
        style={accent ? { color: accent } : undefined}
      >
        {value}
      </div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}
