/**
 * Static diagrams for the encoder section of the motors-drivers lesson.
 * The waveforms use the same model as tools/sim/models/encoder_sim.py:
 * a 6-pole disc (3 N+S periods of 120° per motor turn), sensor B a quarter period (30°) behind A.
 */

const POLES = 6;
const PERIOD_DEG = 360 / (POLES / 2);
const OFFSET_DEG = PERIOD_DEG / 4;

function hall(angleDeg: number): number {
  const a = ((angleDeg % PERIOD_DEG) + PERIOD_DEG) % PERIOD_DEG;
  return a < PERIOD_DEG / 2 ? 1 : 0;
}

export interface QuadratureTimingProps {
  direction: "forward" | "reverse";
  title: string;
  countLabel: string;
  stateLabel: string;
  axisLabel: string;
}

/** Aligned A/B square waves over 8 states (two magnetic periods), with each AB state and the running x4 count. */
export function QuadratureTiming({ direction, title, countLabel, stateLabel, axisLabel }: QuadratureTimingProps) {
  const n = 8;
  const w = 56;
  const x0 = 64;
  const step = direction === "forward" ? 30 : -30;
  const segs = Array.from({ length: n }, (_, i) => {
    const mid = -15 + step * i;
    return { a: hall(mid), b: hall(mid - OFFSET_DEG), count: direction === "forward" ? i : -i };
  });
  const trace = (key: "a" | "b", yTop: number) => {
    const yLo = yTop + 28;
    let d = "";
    segs.forEach((s, i) => {
      const y = s[key] ? yTop : yLo;
      const x = x0 + i * w;
      d += i === 0 ? `M${x},${y}` : `L${x},${y}`;
      d += `L${x + w},${y}`;
    });
    return d;
  };
  const width = x0 + n * w + 8;
  return (
    <figure className="my-6" data-quadrature={direction}>
      <svg viewBox={`0 0 ${width} 176`} className="w-full max-w-2xl" role="img" aria-label={title}>
        {segs.map((_, i) => (
          <line key={i} x1={x0 + i * w} x2={x0 + i * w} y1={8} y2={150} stroke="#3f3f46" strokeDasharray="3 3" />
        ))}
        <text x={8} y={32} fill="#a1a1aa" fontSize={14}>A</text>
        <text x={8} y={84} fill="#a1a1aa" fontSize={14}>B</text>
        <path d={trace("a", 12)} fill="none" stroke="#38bdf8" strokeWidth={2.5} />
        <path d={trace("b", 64)} fill="none" stroke="#f59e0b" strokeWidth={2.5} />
        <text x={8} y={124} fill="#a1a1aa" fontSize={12}>{stateLabel}</text>
        <text x={8} y={146} fill="#a1a1aa" fontSize={12}>{countLabel}</text>
        {segs.map((s, i) => (
          <g key={i}>
            <text x={x0 + i * w + w / 2} y={124} fill="#e4e4e7" fontSize={14} textAnchor="middle" fontFamily="monospace">
              {`${s.a}${s.b}`}
            </text>
            <text x={x0 + i * w + w / 2} y={146} fill="#a1a1aa" fontSize={13} textAnchor="middle" fontFamily="monospace">
              {s.count > 0 ? `+${s.count}` : `${s.count}`}
            </text>
          </g>
        ))}
        <text x={x0 + (n * w) / 2} y={170} fill="#71717a" fontSize={11} textAnchor="middle">
          {axisLabel}
        </text>
      </svg>
      <figcaption className="mt-1 text-sm text-zinc-400">{title}</figcaption>
    </figure>
  );
}

export interface EncoderDiscProps {
  title: string;
  sensorA: string;
  sensorB: string;
}

/** The magnetic disc seen from the rear of the motor: 6 alternating poles, Hall sensors A and B 30° apart. */
export function EncoderDisc({ title, sensorA, sensorB }: EncoderDiscProps) {
  const cx = 110;
  const cy = 126;
  const r = 70;
  const pt = (deg: number, rad: number) => {
    const t = ((deg - 90) * Math.PI) / 180;
    return [cx + rad * Math.cos(t), cy + rad * Math.sin(t)];
  };
  const sectors = Array.from({ length: POLES }, (_, i) => {
    const a0 = i * (360 / POLES);
    const a1 = a0 + 360 / POLES;
    const [x0, y0] = pt(a0, r);
    const [x1, y1] = pt(a1, r);
    const [lx, ly] = pt(a0 + 180 / POLES, r * 0.62);
    return { d: `M${cx},${cy} L${x0},${y0} A${r},${r} 0 0 1 ${x1},${y1} Z`, north: i % 2 === 0, lx, ly };
  });
  const sensor = (deg: number, label: string, color: string) => {
    const [x, y] = pt(deg, r + 14);
    const [tx, ty] = pt(deg, r + 34);
    return (
      <g>
        <rect x={x - 7} y={y - 7} width={14} height={14} fill={color} transform={`rotate(${deg} ${x} ${y})`} />
        <text x={tx} y={ty + 4} fill={color} fontSize={13} textAnchor="middle">{label}</text>
      </g>
    );
  };
  return (
    <figure className="my-6">
      <svg viewBox="0 0 220 250" className="mx-auto w-full max-w-[16rem]" role="img" aria-label={title}>
        {sectors.map((s, i) => (
          <g key={i}>
            <path d={s.d} fill={s.north ? "#7f1d1d" : "#1e3a8a"} stroke="#18181b" />
            <text x={s.lx} y={s.ly + 5} fill="#e4e4e7" fontSize={14} textAnchor="middle">{s.north ? "N" : "S"}</text>
          </g>
        ))}
        <circle cx={cx} cy={cy} r={8} fill="#a1a1aa" />
        {sensor(0, sensorA, "#38bdf8")}
        {sensor(OFFSET_DEG, sensorB, "#f59e0b")}
      </svg>
      <figcaption className="mt-1 text-center text-sm text-zinc-400">{title}</figcaption>
    </figure>
  );
}
