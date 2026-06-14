// Hand-rolled SVG diurnal load profile (brief §3 keeps the prototype's chart).
// Two lines: working days (amber) vs off days (cool blue), mean kW by hour.

export default function LoadProfileChart({
  working,
  off,
  occupiedStart,
  occupiedEnd,
}: {
  working: number[];
  off: number[];
  occupiedStart: number;
  occupiedEnd: number;
}) {
  const W = 720;
  const H = 260;
  const padL = 44;
  const padB = 28;
  const padT = 12;
  const padR = 12;
  const max = Math.max(1, ...working, ...off) * 1.1;
  const innerW = W - padL - padR;
  const innerH = H - padT - padB;

  const x = (h: number) => padL + (h / 23) * innerW;
  const y = (v: number) => padT + innerH - (v / max) * innerH;

  const path = (data: number[]) =>
    data
      .map(
        (v, h) => `${h === 0 ? "M" : "L"}${x(h).toFixed(1)},${y(v).toFixed(1)}`,
      )
      .join(" ");

  const yTicks = 4;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      role="img"
      aria-label="Load profile by hour"
    >
      {/* occupied window shading */}
      <rect
        x={x(occupiedStart)}
        y={padT}
        width={Math.max(0, x(occupiedEnd) - x(occupiedStart))}
        height={innerH}
        fill="#f4b740"
        opacity={0.06}
      />
      {/* y grid + labels */}
      {Array.from({ length: yTicks + 1 }).map((_, i) => {
        const v = (max / yTicks) * i;
        return (
          <g key={i}>
            <line
              x1={padL}
              x2={W - padR}
              y1={y(v)}
              y2={y(v)}
              stroke="#22323f"
              strokeWidth={1}
            />
            <text
              x={padL - 6}
              y={y(v) + 3}
              textAnchor="end"
              fontSize={10}
              fill="#7c93a3"
            >
              {Math.round(v)}
            </text>
          </g>
        );
      })}
      {/* x labels every 3h */}
      {[0, 3, 6, 9, 12, 15, 18, 21].map((h) => (
        <text
          key={h}
          x={x(h)}
          y={H - 8}
          textAnchor="middle"
          fontSize={10}
          fill="#7c93a3"
        >
          {String(h).padStart(2, "0")}
        </text>
      ))}
      <path d={path(off)} fill="none" stroke="#5b8fc7" strokeWidth={2} />
      <path d={path(working)} fill="none" stroke="#f4b740" strokeWidth={2} />
      {/* legend */}
      <g transform={`translate(${W - 180},${padT + 4})`} fontSize={11}>
        <rect x={0} y={-8} width={10} height={3} fill="#f4b740" />
        <text x={16} y={-3} fill="#c7d3dc">
          Working days
        </text>
        <rect x={0} y={8} width={10} height={3} fill="#5b8fc7" />
        <text x={16} y={13} fill="#c7d3dc">
          Off days
        </text>
      </g>
    </svg>
  );
}
