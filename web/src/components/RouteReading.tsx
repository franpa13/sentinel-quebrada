import type { RouteBand, RouteWeek } from "@/lib/types";

const BAND_LABEL: Record<RouteBand, string> = {
  baja: "Baja",
  media: "Media",
  alta: "Alta",
  muy_alta: "Muy alta",
  atencion: "Atención",
};

const BAND_COLOR: Record<RouteBand, string> = {
  baja: "#1f9d62",
  media: "#d6a63a",
  alta: "#e07a32",
  muy_alta: "#d4544c",
  atencion: "#d6a63a",
};

const CLIENT_TITLE: Record<RouteBand, string> = {
  baja: "La semana no se parece a un corte",
  media: "Conviene mirar antes de salir",
  alta: "Hay motivos para no apurarse",
  muy_alta: "Hay motivos para no apurarse",
  atencion: "Todavía no te digo que está libre",
};

function tripLine(name: string) {
  if (name === "Volcán") return "Estás en Volcán. Esta lectura es la de la ruta en tu pueblo, esta semana.";
  return `Salís de Volcán hacia ${name} por la única ruta. La lectura es la de ese punto: un corte en el medio también te deja adentro.`;
}

export function RouteReading({ route }: { route: RouteWeek }) {
  const band = route.operational ?? "atencion";
  return <article className="reading" aria-label={`Chance de corte en ${route.place.name}`}>
    <header><span>{route.place.name === "Volcán" ? "Tu pueblo, esta semana" : `Hacia ${route.place.name}`}</span><h2>{CLIENT_TITLE[band]}</h2></header>
    <p className="exposure">{tripLine(route.place.name)}</p>
    <div className="score"><div><strong>{route.chance === null ? "—" : route.chance.toLocaleString("es-AR")}</strong><span> / 100</span></div>
      <span className="status"><i style={{ background: BAND_COLOR[band] }} />{BAND_LABEL[band]} · {route.place.name}</span>
    </div>
    <p className="exposure">{route.headline}</p>
    <dl className="vitals">
      <div><dt>Lluvia de la semana</dt><dd>{route.week.rain_sum_mm ?? "—"} <small>mm</small></dd><small>{route.week.from} a {route.week.to}</small></div>
      <div><dt>Día más alto</dt><dd>{route.week.peak_index ?? "—"}</dd><small>{route.week.peak_day ?? "sin día"}</small></div>
    </dl>
    <h3>Por qué esa chance</h3>
    <ul className="contributions">{route.factors.map(factor => <li key={factor.id}>
      <details><summary><span>{factor.label}</span><b>+{factor.points.toLocaleString("es-AR")}</b></summary><p>{factor.detail}</p></details>
    </li>)}</ul>
    <details className="conditions" open><summary>Cortes publicados cerca</summary>
      {route.analogs.map(item => <p key={item.episode}><b>{item.date} · {item.place}.</b> {item.summary} <a href={item.url} target="_blank" rel="noreferrer">{item.source}</a></p>)}
    </details>
    <details className="conditions"><summary>Suelo y pendiente de este punto</summary>
      <p>{route.aluvional.terrain.note} Cota {route.aluvional.terrain.elevation_m ?? "—"} m, pendiente {route.aluvional.terrain.slope_deg ?? "—"}°.</p>
      <p>{route.aluvional.soil.note}</p>
    </details>
    <p className="exposure">{route.limits[0]}</p>
  </article>;
}
