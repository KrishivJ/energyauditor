// Hand-rolled SVG diurnal load profile. Two lines: working days (amber) vs off
// days (cool blue), mean kW by hour. Lines draw in on mount; hovering shows a
// crosshair, dots and a tooltip reading both series at that hour.

import { useRef, useState } from "react";

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
  const svgRef = useRef<SVGSVGElement>(null);
  const [hover, setHover] = useState<number | null>(null);

  const onMove = (e: React.MouseEvent) => {
    const svg = svgRef.current;
    if (!svg) return;
    const rect = svg.getBoundingClientRect();
    const px = ((e.clientX - rect.left) / rect.width) * W;
    const h = Math.round(((px - padL) / innerW) * 23);
    setHover(Math.max(0, Math.min(23, h)));
  };

  // Tooltip box geometry, clamped so it never spills past the plot edges.
  const tipW = 116;
  const tipH = 54;
  const tipX = hover === null ? 0 : Math.min(W - padR - tipW, Math.max(padL, x(hover) + 10));
  const tipY = padT + 6;

  return (
    <svg
      ref={svgRef}
      viewBox={`0 0 ${W} ${H}`}
      className="w-full select-none"
      role="img"
      aria-label="Load profile by hour"
      onMouseMove={onMove}
      onMouseLeave={() => setHover(null)}
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

      {/* lines (draw in on mount via stroke-dashoffset) */}
      <path
        className="anim-draw"
        pathLength={1}
        d={path(off)}
        fill="none"
        stroke="#5b8fc7"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        className="anim-draw"
        pathLength={1}
        style={{ animationDelay: "0.15s" }}
        d={path(working)}
        fill="none"
        stroke="#f4b740"
        strokeWidth={2}
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* hover crosshair + markers + tooltip */}
      {hover !== null && (
        <g>
          <line
            x1={x(hover)}
            x2={x(hover)}
            y1={padT}
            y2={padT + innerH}
            stroke="#7c93a3"
            strokeWidth={1}
            strokeDasharray="3 3"
          />
          <circle cx={x(hover)} cy={y(off[hover])} r={3.5} fill="#5b8fc7" />
          <circle cx={x(hover)} cy={y(working[hover])} r={3.5} fill="#f4b740" />
          <g className="anim-fade-in">
            <rect
              x={tipX}
              y={tipY}
              width={tipW}
              height={tipH}
              rx={6}
              fill="#0c1116"
              stroke="#22323f"
            />
            <text x={tipX + 10} y={tipY + 17} fontSize={11} fill="#e6edf3">
              {String(hover).padStart(2, "0")}:00
            </text>
            <circle cx={tipX + 12} cy={tipY + 31} r={3} fill="#f4b740" />
            <text x={tipX + 22} y={tipY + 34} fontSize={10} fill="#c7d3dc">
              Working {Math.round(working[hover])} kW
            </text>
            <circle cx={tipX + 12} cy={tipY + 45} r={3} fill="#5b8fc7" />
            <text x={tipX + 22} y={tipY + 48} fontSize={10} fill="#c7d3dc">
              Off {Math.round(off[hover])} kW
            </text>
          </g>
        </g>
      )}

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
