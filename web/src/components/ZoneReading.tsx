import { LEVEL_COLOR, LEVEL_LABEL, type ZoneScore } from "@/lib/types";

export function ZoneReading({ zone }: { zone: ZoneScore }) {
  return <article className="reading" aria-label={`Ficha de ${zone.name}`}>
    <header><span>Ficha de zona</span><h2>{zone.name}</h2></header>
    <div className="score"><div><strong>{Math.round(zone.index)}</strong><span> / 100</span></div>
      <span className="status"><i style={{background: LEVEL_COLOR[zone.operational_level]}} />{LEVEL_LABEL[zone.operational_level]}</span>
    </div>
    {zone.fast_trigger && <p className="notice"><b>Fast-trigger.</b> {zone.fast_trigger_reason}</p>}
    {zone.confidence_note && <p className="notice">{zone.level !== zone.operational_level && `Nivel físico: ${zone.level}. `}{zone.confidence_note}</p>}
    <dl className="vitals">
      <div><dt>Margen estimado</dt><dd>{Math.round(zone.reaction_margin_min)} <small>min</small></dd><small>Concentración: {Math.round(zone.concentration_min)} min</small></div>
      <div><dt>Confianza del dato</dt><dd>{Math.round(zone.confidence*100)}<small>%</small></dd><small>Edad: {Math.round(zone.snapshot.data_age_min)} min</small></div>
    </dl>
    <h3>Aportes al índice</h3>
    <ul className="contributions">{zone.factors.map(factor => <li key={factor.id}>
      <details><summary><span>{factor.label}</span><b>+{factor.points.toLocaleString("es-AR")}</b></summary><p>{factor.detail}</p></details>
    </li>)}</ul>
    <details className="conditions"><summary>Suelo y terreno</summary>{zone.modifiers.map(m =>
      <p key={m.id}><b>{m.label} ×{m.factor.toFixed(2)}.</b> {m.detail}</p>)}</details>
    {zone.exposure >= .75 && <p className="exposure">Exposición alta: personas o infraestructura crítica.</p>}
  </article>;
}
