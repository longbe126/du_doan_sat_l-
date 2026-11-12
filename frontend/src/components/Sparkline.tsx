import React from "react";

interface SparklineProps {
  values?: number[];
  vmax: number;
  t: number; // current hour (0..24)
  refVal?: number;
  col?: string; // color for current dot
}

export const Sparkline: React.FC<SparklineProps> = ({
  values,
  vmax,
  t,
  refVal,
  col = "#d4e88a",
}) => {
  // If values is not supplied or empty, synthesize a smooth ramp based on t and vmax
  const safeVmax = vmax > 0 ? vmax : 1;
  const safeT = Math.max(0, Math.min(24, Math.round(t)));

  const vals: number[] = React.useMemo(() => {
    if (values && values.length >= 25) {
      return values;
    }
    // Fallback ramp if series is loading
    const arr: number[] = [];
    for (let h = 0; h <= 24; h++) {
      const r = 0.3 + 0.7 * Math.pow(h / 24, 1.3);
      arr.push(r * safeVmax * 0.7);
    }
    return arr;
  }, [values, safeVmax]);

  // Calculate 6 sample points from 0 to t
  const { xs, ys, lineY, lastX, lastY } = React.useMemo(() => {
    const rawIdx: number[] = [];
    const count = 6;
    for (let i = 0; i < count; i++) {
      rawIdx.push(Math.round((i * safeT) / (count - 1)));
    }
    const idx = Array.from(new Set(rawIdx));

    const computedYs = idx.map((i) => {
      const val = vals[i] !== undefined ? vals[i] : 0;
      const ratio = Math.min(Math.max(val / safeVmax, 0), 1);
      return 48 - 40 * ratio;
    });

    const computedXs =
      idx.length > 1
        ? idx.map((_, i) => 12 + (i * (188 - 12)) / (idx.length - 1))
        : [188];

    const lY =
      refVal !== undefined && refVal !== null
        ? 48 - 40 * Math.min(Math.max(refVal / safeVmax, 0), 1)
        : null;

    const lX = computedXs[computedXs.length - 1];
    const lYDot = computedYs[computedYs.length - 1];

    return {
      xs: computedXs,
      ys: computedYs,
      lineY: lY,
      lastX: lX,
      lastY: lYDot,
    };
  }, [vals, safeVmax, safeT, refVal]);

  return (
    <svg className="w-full h-[30px] mt-1.5 rounded-lg overflow-hidden bg-white/[0.035]" viewBox="0 0 200 56">
      {lineY !== null && (
        <line
          x1="0"
          x2="200"
          y1={lineY}
          y2={lineY}
          stroke="rgba(255,255,255,0.35)"
          strokeWidth="1"
          strokeDasharray="4 3"
        />
      )}
      {xs.slice(0, -1).map((x, i) => (
        <circle key={i} cx={x} cy={ys[i]} r="2.6" fill="#ffffff" opacity="0.9" />
      ))}
      <circle cx={lastX} cy={lastY} r="3.4" fill={col} />
      <circle
        cx={lastX}
        cy={lastY}
        r="8"
        fill="none"
        stroke={col}
        strokeWidth="1.2"
        className="animate-pulse"
      />
    </svg>
  );
};
