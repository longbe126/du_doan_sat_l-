import React from "react";

interface DotGaugeProps {
  value: number; // 0 to 1
  level?: "low" | "mid" | "high";
  dots?: number;
  activeDotIndex?: number;
}

export const DotGauge: React.FC<DotGaugeProps> = ({
  value,
  level = "high",
  dots = 5,
  activeDotIndex,
}) => {
  const targetIndex =
    activeDotIndex !== undefined
      ? activeDotIndex
      : Math.min(dots - 1, Math.max(0, Math.round(value * (dots - 1))));

  const colorMap = {
    low: "#10b981",
    mid: "#f59e0b",
    high: "#ef4444",
  };
  const activeColor = colorMap[level] || colorMap.high;

  return (
    <div className="w-full py-1">
      <svg className="w-full h-3 overflow-visible" viewBox="0 0 100 12">
        {/* Baseline connecting line */}
        <line
          x1="6"
          y1="6"
          x2="94"
          y2="6"
          stroke="rgba(255, 255, 255, 0.14)"
          strokeWidth="1.2"
        />

        {/* 5 Dots */}
        {Array.from({ length: dots }).map((_, i) => {
          const cx = 6 + (i * 88) / (dots - 1);
          const isTarget = i === targetIndex;

          return (
            <g key={i}>
              {isTarget && (
                <circle
                  cx={cx}
                  cy="6"
                  r="4.8"
                  fill="none"
                  stroke={activeColor}
                  strokeWidth="1.2"
                />
              )}
              <circle
                cx={cx}
                cy="6"
                r={isTarget ? "2.2" : "1.8"}
                fill={isTarget ? activeColor : "rgba(255, 255, 255, 0.22)"}
              />
            </g>
          );
        })}
      </svg>
    </div>
  );
};
