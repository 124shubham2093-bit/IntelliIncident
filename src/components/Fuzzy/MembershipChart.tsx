import React from 'react';
import { MembershipCurveDefinition } from '@/data/demoFuzzy';

interface MembershipChartProps {
  curveDef: MembershipCurveDefinition;
  currentValue: number;
}

export const MembershipChart: React.FC<MembershipChartProps> = ({ curveDef, currentValue }) => {
  // SVG coordinate dimensions
  const svgWidth = 460;
  const svgHeight = 160;
  const padding = { top: 20, right: 30, bottom: 30, left: 35 };

  const plotWidth = svgWidth - padding.left - padding.right;
  const plotHeight = svgHeight - padding.top - padding.bottom;

  // Scale functions
  const scaleX = (val: number) => {
    const clamped = Math.max(curveDef.min, Math.min(val, curveDef.max));
    return padding.left + ((clamped - curveDef.min) / (curveDef.max - curveDef.min)) * plotWidth;
  };

  const scaleY = (mu: number) => {
    return padding.top + (1 - mu) * plotHeight;
  };

  // Convert points to SVG polyline path
  const makePointsString = (points: { x: number; y: number }[]) => {
    return points
      .map((p) => `${scaleX(p.x)},${scaleY(p.y)}`)
      .join(' ');
  };

  const currentX = scaleX(currentValue);

  return (
    <div className="bg-slate-950/80 border border-slate-800 rounded-lg p-3.5">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono font-semibold text-slate-200">
            {curveDef.name}
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            [{curveDef.min} - {curveDef.max} {curveDef.unit}]
          </span>
        </div>
        <div className="flex items-center gap-3">
          {curveDef.sets.map((s) => (
            <div key={s.label} className="flex items-center gap-1.5 text-[10px] font-mono">
              <span
                className="w-2.5 h-1.5 rounded-sm inline-block"
                style={{ backgroundColor: s.color }}
              />
              <span className="text-slate-300">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="relative">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-auto overflow-visible select-none"
        >
          {/* Grid lines */}
          <line
            x1={padding.left}
            y1={scaleY(0)}
            x2={padding.left + plotWidth}
            y2={scaleY(0)}
            stroke="#334155"
            strokeWidth="1"
          />
          <line
            x1={padding.left}
            y1={scaleY(0.5)}
            x2={padding.left + plotWidth}
            y2={scaleY(0.5)}
            stroke="#1e293b"
            strokeDasharray="3 3"
            strokeWidth="1"
          />
          <line
            x1={padding.left}
            y1={scaleY(1)}
            x2={padding.left + plotWidth}
            y2={scaleY(1)}
            stroke="#334155"
            strokeWidth="1"
          />

          {/* Y Axis labels: mu = 0.0, 0.5, 1.0 */}
          <text
            x={padding.left - 6}
            y={scaleY(1) + 4}
            textAnchor="end"
            fontSize="9"
            fill="#64748b"
            fontFamily="monospace"
          >
            1.0
          </text>
          <text
            x={padding.left - 6}
            y={scaleY(0.5) + 3}
            textAnchor="end"
            fontSize="9"
            fill="#64748b"
            fontFamily="monospace"
          >
            0.5
          </text>
          <text
            x={padding.left - 6}
            y={scaleY(0) + 3}
            textAnchor="end"
            fontSize="9"
            fill="#64748b"
            fontFamily="monospace"
          >
            0.0
          </text>

          {/* Fuzzy Membership Curves */}
          {curveDef.sets.map((s) => (
            <g key={s.label}>
              <polyline
                points={makePointsString(s.points)}
                fill="none"
                stroke={s.color}
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                opacity="0.85"
              />
            </g>
          ))}

          {/* Current Input Value Vertical Cursor */}
          <line
            x1={currentX}
            y1={padding.top - 6}
            x2={currentX}
            y2={padding.top + plotHeight}
            stroke="#22d3ee"
            strokeWidth="2"
            strokeDasharray="4 2"
          />
          <circle cx={currentX} cy={scaleY(0)} r="4" fill="#22d3ee" />

          {/* Value Badge on X-Axis */}
          <rect
            x={currentX - 24}
            y={padding.top + plotHeight + 6}
            width="48"
            height="18"
            rx="3"
            fill="#0f172a"
            stroke="#22d3ee"
            strokeWidth="1"
          />
          <text
            x={currentX}
            y={padding.top + plotHeight + 19}
            textAnchor="middle"
            fontSize="10"
            fontWeight="bold"
            fill="#22d3ee"
            fontFamily="monospace"
          >
            {currentValue}
          </text>

          {/* Min & Max X Labels */}
          <text
            x={padding.left}
            y={padding.top + plotHeight + 16}
            textAnchor="start"
            fontSize="9"
            fill="#64748b"
            fontFamily="monospace"
          >
            {curveDef.min}
          </text>
          <text
            x={padding.left + plotWidth}
            y={padding.top + plotHeight + 16}
            textAnchor="end"
            fontSize="9"
            fill="#64748b"
            fontFamily="monospace"
          >
            {curveDef.max}
          </text>
        </svg>
      </div>
    </div>
  );
};
