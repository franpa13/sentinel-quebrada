import { LEVEL_COLOR, type RouteWeek, type ScenarioDetail, type ScenarioMeta, type Snapshot, type ZoneScore } from "@/lib/types";
import { BasinPlate } from "./BasinPlate";
import { Road } from "./Road";
import { RouteReading } from "./RouteReading";
import { ZoneReading } from "./ZoneReading";

const knobs = [
  ["rain_acc_mm", "Acumulada 6–24 h", "mm", 140, 1],
  ["intensity_mm_h", "Intensidad", "mm/h", 80, 1],
  ["burst_mm_30min", "Ráfaga de 30 min", "mm", 50, 1],
  ["soil_moisture", "Humedad del suelo", "", 1, .01],
  ["data_age_min", "Edad del dato", "min", 480, 5],
] as const;

type Props = {
  catalog: ScenarioMeta[]; scenario: ScenarioDetail | null; frameIndex: number; playing: boolean;
  mode: "scenario" | "manual" | "meteo" | "ruta"; zones: ZoneScore[]; selected?: ZoneScore; narrative: string;
  knobs: Snapshot; note?: string; error: string | null; connecting: boolean; meteoBusy: boolean;
  route: RouteWeek | null; routeBusy: boolean; townName: string;
  choose: (id: string) => void; select: (id: string) => void; step: (n: number) => void; toggle: () => void;
  evaluate: (s: Snapshot) => void; meteo: () => void; retry: () => void; pickTown: (name: string) => void;
};

export function Atlas(p: Props) {
  const frames = p.scenario?.frames ?? [];
  const frame = p.mode === "scenario" ? frames[p.frameIndex] : null;
  const source = p.mode === "ruta" ? "Lectura real de la RN9" : p.mode === "scenario" ? "Escenario simulado" : p.mode === "manual" ? "Pluviómetro simulado" : "Contexto de grilla";
  const place = "Volcán, Jujuy";
  const title = p.mode === "ruta" ? "¿Hasta dónde vas?" : "Recorrido de la quebrada";
  return <div className="atlas">
    <header className="mast"><div className="brand">
      <svg viewBox="0 0 46 37" aria-hidden="true"><path d="M2 31 17 5l8 13 5-8 14 21H2Zm9-5 6-10 7 11m1-9 5 8" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinejoin="round"/></svg>
      Sentinel Quebrada</div><span>Alerta temprana aluvional</span></header>
    <main className="sheet">
      <div className="sheet-head"><div><p>{place}</p><h1>{title}</h1></div>
        <div className="tools">
          <label className="scenario">Simulación
            <select disabled={!p.catalog.length} value={p.mode === "scenario" ? (p.scenario?.id ?? "") : ""} onChange={e=>p.choose(e.target.value)}>
              <option value="" disabled>{p.mode !== "scenario" ? source : "Seleccionar"}</option>
              {p.catalog.map(s=><option key={s.id} value={s.id}>{s.title}</option>)}
            </select>
          </label>
          <details className="instrument" onKeyDown={e=>{
            if(e.key === "Escape") {
              e.currentTarget.open = false;
              e.currentTarget.querySelector("summary")?.focus();
            }
          }}><summary>Ajustar lecturas</summary>
            <div className="instrument-body"><h2>Pluviómetro simulado</h2><p>Lectura en la cuenca alta.</p>
              {knobs.map(([field,label,unit,max,step]) => <label key={field}><span>{label}<b>{p.knobs[field]} {unit}</b></span>
                <input type="range" min={0} max={max} step={step} value={p.knobs[field]} onChange={e=>p.evaluate({...p.knobs,[field]:Number(e.target.value)})} /></label>)}
              <button onClick={p.meteo} disabled={p.meteoBusy}>{p.meteoBusy ? "Consultando…" : "Consultar Open-Meteo"}</button>
              {p.note && <p>{p.note}</p>}
            </div>
          </details>
        </div>
      </div>
      <Road townName={p.townName} busy={p.routeBusy} onPick={p.pickTown}/>
      {p.error && <div className="error" role="alert">{p.error} {!p.catalog.length && <button onClick={p.retry} disabled={p.connecting}>Reintentar</button>}</div>}
      <div className="spread">
        <div className="survey">
          <BasinPlate zones={p.zones} selected={p.selected?.zone_id} onSelect={id=>{
            p.select(id);
            if (window.matchMedia("(max-width:1023px)").matches) document.getElementById("zone-reading")?.focus();
          }}/>
          <section className="sequence" aria-label="Reproducción">
            <button className="play" onClick={p.toggle} disabled={!frames.length}>
              <svg viewBox="0 0 16 16" aria-hidden="true">{p.playing ? <path d="M3 2h4v12H3zm6 0h4v12H9z"/> : <path d="M3 1v14l11-7z"/>}</svg>
              {p.playing ? "Pausa" : "Reproducir"}
            </button>
            <div className="time"><div><span>{source}</span><strong>{p.mode === "ruta" ? (p.routeBusy ? "Consultando la semana…" : (p.route?.week.peak_day ?? "Sin semana")) : (frame?.label ?? (p.mode === "scenario" ? "Sin lectura" : "Lectura actual"))}</strong></div>
              {frames.length > 0 && <input className="scrub" type="range" aria-label="Paso del escenario" min={0} max={frames.length-1} value={p.frameIndex} aria-valuetext={frames[p.frameIndex]?.label} disabled={frames.length===1} onChange={e=>p.step(Number(e.target.value))}/>}
              <div className="ticks" aria-label="Pasos del escenario">{frames.map((f,i)=>{
                const cue=f.zones.find(z=>z.zone_id==="cuenca_alta");
                return <button key={f.index} title={f.label} aria-label={`Paso ${i+1}, ${f.label}`} aria-current={i===p.frameIndex && frame ? "step":undefined} onClick={()=>p.step(i)}>
                  <i style={{background:cue ? LEVEL_COLOR[cue.operational_level] : undefined}}/></button>;
              })}</div>
            </div>
          </section>
          <p className="caption">{p.routeBusy && p.mode === "ruta" ? "Consultando lluvia, suelo y cortes publicados de la RN9…" : p.narrative || (p.connecting ? "Cargando el escenario local…" : "No hay lecturas disponibles.")}</p>
          {p.mode === "ruta" && <p className="caption map-note">El dibujo sigue siendo el esquema de Volcán. La ficha es la ruta en {p.townName}, con la lluvia de esta semana y los cortes publicados.</p>}
        </div>
        <aside className="inspector" id="zone-reading" tabIndex={-1}>{p.mode === "ruta" && p.routeBusy ? <p>Consultando la RN9…</p> : p.mode === "ruta" && p.route ? <>
          <RouteReading route={p.route}/>
        </> : p.selected ? <>
          <ZoneReading zone={p.selected}/><button className="to-route" onClick={()=>document.querySelector<HTMLButtonElement>(".site[aria-pressed=true]")?.focus()}>Volver al recorrido</button>
        </> : <p>{p.routeBusy ? "Consultando la RN9…" : "Esperando datos del motor."}</p>}</aside>
      </div>
    </main>
    <footer>{p.mode === "ruta" ? "La chance sale de la lluvia de esta semana y de cortes publicados. No es un parte de Vialidad ni una orden de cancelar la excursión." : "Esquema de simulación. No es cartografía oficial ni una orden de evacuación. Kirpich estima el tiempo de concentración, no la llegada de una colada."}</footer>
  </div>;
}
