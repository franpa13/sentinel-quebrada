import { LEVEL_COLOR, LEVEL_LABEL, LEVELS, type ZoneScore } from "@/lib/types";

const sites: Record<string, [number, number]> = {
  cuenca_alta: [17, 17], cauce: [31, 33], cono: [45, 47],
  casco: [59, 61], accesos: [70, 75], rn9: [81, 88],
};
const channel = "M 28 -25 C 86 3 72 67 170 85 S 208 127 310 165 S 359 206 450 235 S 491 277 590 305 S 628 349 700 375 S 737 419 810 440 S 935 467 976 525";

// Closed, nested contour lines suggest relief without claiming measured elevations.
function hill(cx: number, cy: number, width: number, height: number, phase: number) {
  return Array.from({ length: 23 }, (_, i) => {
    const radius = 1 - i / 25;
    const points = Array.from({ length: 160 }, (_, j) => {
      const a = j * Math.PI / 80;
      const fold = 1 + .12 * Math.sin(3*a + phase + radius) + .085 * Math.cos(5*a - radius)
        + .04 * Math.cos(9*a + phase) + .026 * Math.sin(14*a + 2*radius);
      return `${(cx + width * radius * fold * Math.cos(a)).toFixed(1)},${(cy + height * radius * fold * Math.sin(a)).toFixed(1)}`;
    });
    return <polygon key={i} points={points.join(" ")} fill={i % 5 === 0 ? "#82794c" : "none"}
      fillOpacity=".046" stroke="#897e57" strokeOpacity={i % 5 === 0 ? ".51" : ".29"} strokeWidth={i % 5 === 0 ? 1.4 : .85} />;
  });
}

const relief = <g>{hill(106, 465, 415, 250, 2)}{hill(860, 37, 445, 238, 1)}{hill(-68, 90, 136, 200, 4)}</g>;

export function BasinPlate({ zones, selected, onSelect }: {
  zones: ZoneScore[]; selected?: string; onSelect: (id: string) => void;
}) {
  return <section className="plate" aria-label="Recorrido esquemático de la quebrada">
    <header className="plate-cap"><span>Cuenca de Volcán</span><span>Esquema sin escala</span></header>
    <div className="terrain">
      <svg aria-hidden="true" viewBox="0 0 1000 500" preserveAspectRatio="none">
        {relief}
        <g fill="none" stroke="#759da0" strokeWidth="2" opacity=".74">
          <path d="M200 -12 Q166 46 182 55 T170 85 M390 -22 C301 37 391 70 290 99 S259 151 310 165 M-10 178 C55 151 118 245 211 218 S335 245 450 235 M552 530 C589 433 472 428 513 361 S572 345 590 305 M930 217 Q876 297 802 299 T700 375" />
        </g>
        <path d={channel} fill="none" stroke="#a5c5be" strokeWidth="19" opacity=".75" />
        <path d={channel} fill="none" stroke="#407f83" strokeWidth="6" />
        <path d="M640 520 Q785 426 810 440 T1040 329" fill="none" stroke="#797565" strokeWidth="6"/>
        <path d="M640 520 Q785 426 810 440 T1040 329" fill="none" stroke="#faf6e9" strokeDasharray="7 5" strokeWidth="2"/>
      </svg>
      <span className="headwater">Aguas arriba</span><span className="outflow">Aguas abajo</span>
      {zones.map(zone => {
        const point = sites[zone.zone_id];
        if (!point) return null;
        return <button key={zone.zone_id} className={`site ${point[0] > 55 ? "west" : ""}`} type="button"
          style={{ left: `${point[0]}%`, top: `${point[1]}%` }}
          aria-pressed={zone.zone_id === selected} onClick={() => onSelect(zone.zone_id)}>
          <i style={{ background: LEVEL_COLOR[zone.operational_level] }} />
          <span><strong>{zone.name}</strong><small>{LEVEL_LABEL[zone.operational_level]} · {Math.round(zone.index)}{zone.fast_trigger && " · Fast-trigger"}</small></span>
        </button>;
      })}
    </div>
    <div className="key" aria-label="Leyenda de niveles">{LEVELS.map(level =>
      <span key={level}><i style={{ background: LEVEL_COLOR[level] }} />{LEVEL_LABEL[level]}</span>)}</div>
  </section>;
}
