"use client";

import { useEffect, useState } from "react";
import { evaluate, getScenario, listScenarios, openMeteo } from "@/lib/api";
import { LEVEL_COLOR, LEVEL_LABEL, type Level, type ScenarioDetail, type ScenarioMeta, type Snapshot, type ZoneScore } from "@/lib/types";

const DEFAULT_SCENARIO = "pico_cuenca_alta";

const EMPTY_SNAPSHOT: Snapshot = {
  rain_acc_mm: 8,
  intensity_mm_h: 3,
  burst_mm_30min: 0,
  soil_moisture: 0.38,
  data_age_min: 5,
  sensor_quality: 0.95,
};

export function Dashboard() {
  const [catalog, setCatalog] = useState<ScenarioMeta[]>([]);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedId, setSelectedId] = useState("cuenca_alta");
  const [mode, setMode] = useState<"scenario" | "manual" | "meteo">("scenario");
  const [manual, setManual] = useState<{ narrative: string; zones: ZoneScore[]; note?: string } | null>(null);
  const [knobs, setKnobs] = useState<Snapshot>(EMPTY_SNAPSHOT);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const listed = await listScenarios();
        const detail = await getScenario(DEFAULT_SCENARIO);
        if (cancelled) return;
        setCatalog(listed.scenarios);
        setScenario(detail);
        setError(null);
      } catch {
        if (!cancelled) {
          setError("El motor de Python no está corriendo en el puerto 8000.");
        }
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!playing || mode !== "scenario" || !scenario) return;
    const timer = window.setInterval(() => {
      setFrameIndex((current) => {
        if (current >= scenario.frames.length - 1) {
          setPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, 1400);
    return () => window.clearInterval(timer);
  }, [playing, mode, scenario]);

  const frame = mode === "scenario" ? scenario?.frames[frameIndex] : null;
  const zones = mode === "scenario" ? (frame?.zones ?? []) : (manual?.zones ?? []);
  const narrative = mode === "scenario" ? (frame?.narrative ?? "") : (manual?.narrative ?? "");
  const selected = zones.find((zone) => zone.zone_id === selectedId) ?? zones[0];

  async function chooseScenario(id: string) {
    setPlaying(false);
    setBusy(true);
    try {
      const detail = await getScenario(id);
      setScenario(detail);
      setFrameIndex(0);
      setMode("scenario");
      setManual(null);
      setError(null);
    } catch {
      setError("No se pudo cargar el escenario.");
    } finally {
      setBusy(false);
    }
  }

  async function runKnobs(next: Snapshot) {
    setKnobs(next);
    setPlaying(false);
    setMode("manual");
    try {
      const result = await evaluate(next);
      setManual(result);
      setError(null);
    } catch {
      setError("El motor no respondió al mover las perillas.");
    }
  }

  async function pullMeteo() {
    setPlaying(false);
    setMode("meteo");
    setBusy(true);
    try {
      const result = await openMeteo();
      setManual({ narrative: result.narrative, zones: result.zones, note: result.disclaimer });
      setKnobs(result.snapshot);
      setError(null);
    } catch {
      setError("Open-Meteo no respondió. Los escenarios locales siguen disponibles.");
      setMode("scenario");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="min-h-full bg-[#101614] text-[#e7f0ea]">
      <header className="flex flex-wrap items-end justify-between gap-4 border-b border-[#2c4036] px-5 py-4">
        <div>
          <p className="text-xs tracking-[0.28em] text-[#d7b48a]">SENTINEL QUEBRADA</p>
          <h1 className="font-serif text-3xl leading-none text-[#f6f1e7]">Alerta temprana aluvional</h1>
          <p className="mt-1 max-w-xl text-sm text-[#9eb1a6]">
            Volcán, Jujuy. No pronostica el clima: cruza lo que ya está pasando en la cuenca y estima el margen.
          </p>
        </div>
        <div className="text-right text-xs text-[#9eb1a6]">
          <p>{mode === "scenario" ? (scenario?.title ?? "Escenario") : mode === "meteo" ? "Contexto Open-Meteo" : "Perillas en vivo"}</p>
          <p className="text-[#f6f1e7]">{frame?.label ?? "Lectura actual"}</p>
        </div>
      </header>

      {error ? (
        <div className="mx-5 mt-4 rounded-xl border border-[#e07a32] bg-[#2a1c12] px-4 py-3 text-sm text-[#f6d7b8]">
          <p>{error}</p>
          <p className="mt-1 text-[#d7b48a]">En la raíz del repo: npm run dev</p>
        </div>
      ) : null}

      <main className="grid gap-4 p-4 lg:h-[calc(100dvh-8.5rem)] lg:grid-cols-[minmax(220px,280px)_minmax(0,1fr)_minmax(240px,300px)] lg:overflow-auto">
        <section className="space-y-4 lg:overflow-auto lg:pr-1">
          <article className="rounded-2xl border border-[#2c4036] bg-[#17211c] p-4">
            <h2 className="text-sm font-medium text-[#d7b48a]">Escenarios</h2>
            <div className="mt-3 space-y-2">
              {catalog.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => chooseScenario(item.id)}
                  className={`w-full rounded-xl border px-3 py-2 text-left ${
                    mode === "scenario" && scenario?.id === item.id
                      ? "border-[#d7b48a] bg-[#24352c]"
                      : "border-[#2c4036] hover:border-[#4d6a5c]"
                  }`}
                >
                  <span className="block text-sm text-[#f6f1e7]">{item.title}</span>
                  <span className="mt-1 block text-xs leading-5 text-[#9eb1a6]">{item.summary}</span>
                </button>
              ))}
              {busy && catalog.length === 0 ? <p className="text-sm text-[#9eb1a6]">Conectando con el motor…</p> : null}
            </div>
            {mode === "scenario" && scenario ? (
              <p className="mt-3 text-xs leading-5 text-[#d7b48a]">{scenario.demo_hint}</p>
            ) : null}
          </article>

          <article className="rounded-2xl border border-[#2c4036] bg-[#17211c] p-4">
            <div className="flex items-center justify-between gap-2">
              <h2 className="text-sm font-medium text-[#d7b48a]">Reproducción</h2>
              <button
                type="button"
                disabled={mode !== "scenario" || !scenario}
                onClick={() => setPlaying((value) => !value)}
                className="rounded-full bg-[#f6f1e7] px-3 py-1 text-xs font-medium text-[#17211c] disabled:opacity-40"
              >
                {playing ? "Pausa" : "Reproducir"}
              </button>
            </div>
            <div className="mt-3 flex flex-wrap gap-1">
              {(scenario?.frames ?? []).map((item, index) => {
                const cue = item.zones.find((zone) => zone.zone_id === "cuenca_alta");
                const color = cue ? LEVEL_COLOR[cue.operational_level] : "#4d6a5c";
                return (
                  <button
                    key={item.index}
                    type="button"
                    title={item.label}
                    onClick={() => {
                      setMode("scenario");
                      setPlaying(false);
                      setFrameIndex(index);
                    }}
                    className="h-8 w-8 rounded-md text-[10px]"
                    style={{
                      background: color,
                      outline: mode === "scenario" && index === frameIndex ? "2px solid #f6f1e7" : "none",
                      color: "#102017",
                    }}
                  >
                    {index + 1}
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-[#9eb1a6]">Cada paso son 10 minutos. El color es el de la cuenca alta.</p>
          </article>

          <article className="rounded-2xl border border-[#2c4036] bg-[#17211c] p-4">
            <h2 className="text-sm font-medium text-[#d7b48a]">Perillas · pluviómetro de cuenca alta</h2>
            <div className="mt-3 space-y-3">
              <Knob label="Acumulada 6–24 h" min={0} max={140} step={1} unit="mm" value={knobs.rain_acc_mm} onChange={(value) => runKnobs({ ...knobs, rain_acc_mm: value })} />
              <Knob label="Intensidad" min={0} max={80} step={1} unit="mm/h" value={knobs.intensity_mm_h} onChange={(value) => runKnobs({ ...knobs, intensity_mm_h: value })} />
              <Knob label="Ráfaga 30 min" min={0} max={50} step={1} unit="mm" value={knobs.burst_mm_30min} onChange={(value) => runKnobs({ ...knobs, burst_mm_30min: value })} />
              <Knob label="Humedad del suelo" min={0} max={1} step={0.01} unit="" value={knobs.soil_moisture} onChange={(value) => runKnobs({ ...knobs, soil_moisture: value })} />
              <Knob label="Edad del dato" min={0} max={480} step={5} unit="min" value={knobs.data_age_min} onChange={(value) => runKnobs({ ...knobs, data_age_min: value })} />
            </div>
            <button type="button" onClick={pullMeteo} className="mt-4 w-full rounded-xl border border-[#4d6a5c] px-3 py-2 text-xs text-[#d7b48a] hover:bg-[#24352c]">
              Traer contexto Open-Meteo
            </button>
            {manual?.note ? <p className="mt-2 text-xs leading-5 text-[#9eb1a6]">{manual.note}</p> : null}
          </article>
        </section>

        <section className="flex min-h-0 flex-col gap-3">
          <div className="min-h-0 flex-1 rounded-3xl border border-[#2c4036] bg-[#0e1612] p-3">
            <BasinMap zones={zones} selectedId={selected?.zone_id} onSelect={setSelectedId} />
          </div>
          <div className="flex flex-wrap gap-2">
            {zones.map((zone) => (
              <button
                key={zone.zone_id}
                type="button"
                onClick={() => setSelectedId(zone.zone_id)}
                className={`rounded-full border px-3 py-1 text-xs ${
                  zone.zone_id === selected?.zone_id ? "border-[#f6f1e7] text-[#f6f1e7]" : "border-[#2c4036] text-[#9eb1a6]"
                }`}
              >
                {zone.name} · {Math.round(zone.index)}
              </button>
            ))}
          </div>
          <blockquote className="rounded-2xl border border-[#2c4036] bg-[#17211c] px-4 py-3 text-sm leading-6 text-[#f6f1e7]">
            {narrative || "Elegí un escenario o mové una perilla."}
          </blockquote>
        </section>

        <section className="lg:overflow-auto lg:pr-1">
          {selected ? <RiskCard zone={selected} /> : <p className="text-sm text-[#9eb1a6]">Sin lectura todavía.</p>}
        </section>
      </main>
      <footer className="px-5 pb-5 text-xs leading-5 text-[#6e8578]">
        Esquema de demo, no cartografía oficial ni una orden de evacuación. El margen usa el tiempo de concentración de Kirpich: orienta minutos, no simula un flujo de detritos en 2D.
      </footer>
    </div>
  );
}

function Knob({
  label,
  min,
  max,
  step,
  unit,
  value,
  onChange,
}: {
  label: string;
  min: number;
  max: number;
  step: number;
  unit: string;
  value: number;
  onChange: (value: number) => void;
}) {
  const shown = step < 1 ? value.toFixed(2) : Math.round(value).toString();
  return (
    <label className="block text-xs text-[#9eb1a6]">
      <span className="flex justify-between">
        <span>{label}</span>
        <span className="text-[#f6f1e7]">
          {shown} {unit}
        </span>
      </span>
      <input
        className="mt-1 w-full accent-[#d7b48a]"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function BasinMap({
  zones,
  selectedId,
  onSelect,
}: {
  zones: ZoneScore[];
  selectedId?: string;
  onSelect: (id: string) => void;
}) {
  return (
    <svg viewBox="0 0 720 780" className="h-full w-full" role="img" aria-label="Esquema de zonas de Volcán" preserveAspectRatio="xMidYMid meet">
      <rect width="720" height="780" rx="28" fill="#0e1612" />
      <text x="36" y="42" fill="#9eb1a6" fontSize="14">
        Aguas arriba
      </text>
      {zones.map((zone) => {
        const active = zone.zone_id === selectedId;
        return (
          <g key={zone.zone_id} onClick={() => onSelect(zone.zone_id)} className="cursor-pointer">
            <path
              d={zone.svg}
              fill={LEVEL_COLOR[zone.operational_level]}
              fillOpacity={active ? 0.95 : 0.78}
              stroke={active ? "#f6f1e7" : "#0e1612"}
              strokeWidth={active ? 6 : 3}
            />
            <text x={zone.label[0]} y={zone.label[1]} textAnchor="middle" fill="#f7f4ee" fontSize="18" fontWeight="600">
              {zone.name}
            </text>
            <text x={zone.label[0]} y={zone.label[1] + 20} textAnchor="middle" fill="#f7f4ee" fontSize="14">
              {LEVEL_LABEL[zone.operational_level]} · {Math.round(zone.index)}
            </text>
            {zone.zone_id === "accesos" ? (
              <text x="566" y="590" textAnchor="middle" fill="#f7f4ee" fontSize="18" fontWeight="600">
                Accesos
              </text>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

function RiskCard({ zone }: { zone: ZoneScore }) {
  const color = LEVEL_COLOR[zone.operational_level];
  const maxPoints = Math.max(...zone.factors.map((factor) => factor.points), 1);
  return (
    <article className="rounded-3xl border border-[#2c4036] bg-[#17211c] p-5">
      <p className="text-xs tracking-[0.18em] text-[#9eb1a6]">{zone.name.toUpperCase()}</p>
      <div className="mt-2 flex items-end justify-between gap-3">
        <p className="font-serif text-7xl leading-none" style={{ color }}>
          {Math.round(zone.index)}
        </p>
        <LevelPill level={zone.operational_level} />
      </div>
      {zone.level !== zone.operational_level ? (
        <p className="mt-2 text-[11px] text-[#d7b48a]">Físico {LEVEL_LABEL[zone.level].toLowerCase()}, operativo más alto por el dato.</p>
      ) : null}
      {zone.fast_trigger ? (
        <p className="mt-4 rounded-xl bg-[#3a1b18] px-3 py-2 text-sm leading-5 text-[#ffd0cb]">
          Fast-trigger. {zone.fast_trigger_reason}
        </p>
      ) : null}
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl bg-[#101614] p-3">
          <p className="text-xs text-[#9eb1a6]">Margen de reacción</p>
          <p className="mt-1 text-2xl text-[#f6f1e7]">{Math.round(zone.reaction_margin_min)} min</p>
          <p className="text-[11px] text-[#6e8578]">Concentración del tramo: {Math.round(zone.concentration_min)} min</p>
        </div>
        <div className="rounded-xl bg-[#101614] p-3">
          <p className="text-xs text-[#9eb1a6]">Confianza del dato</p>
          <p className="mt-1 text-2xl text-[#f6f1e7]">{Math.round(zone.confidence * 100)}%</p>
          <p className="text-[11px] text-[#6e8578]">Edad {Math.round(zone.snapshot.data_age_min)} min</p>
        </div>
      </div>
      {zone.confidence_note ? <p className="mt-3 text-xs leading-5 text-[#e6c15a]">{zone.confidence_note}</p> : null}
      {zone.exposure >= 0.75 ? <p className="mt-2 text-xs text-[#d7b48a]">Exposición alta: personas o infraestructura crítica.</p> : null}
      <h3 className="mt-5 text-xs tracking-[0.16em] text-[#9eb1a6]">QUÉ ARMA EL ÍNDICE</h3>
      <ul className="mt-3 space-y-3">
        {zone.factors.map((factor) => (
          <li key={factor.id}>
            <div className="flex justify-between text-xs">
              <span>{factor.label}</span>
              <span className="text-[#f6f1e7]">+{factor.points.toFixed(0)}</span>
            </div>
            <div className="mt-1 h-1.5 rounded-full bg-[#101614]">
              <div className="h-1.5 rounded-full" style={{ width: `${(factor.points / maxPoints) * 100}%`, background: color }} />
            </div>
            <p className="mt-1 text-[11px] leading-4 text-[#6e8578]">{factor.detail}</p>
          </li>
        ))}
      </ul>
      <ul className="mt-4 space-y-2">
        {zone.modifiers.map((modifier) => (
          <li key={modifier.id} className="text-xs leading-5 text-[#9eb1a6]">
            <span className="text-[#f6f1e7]">{modifier.label}</span> ×{modifier.factor.toFixed(2)}. {modifier.detail}
          </li>
        ))}
      </ul>
    </article>
  );
}

function LevelPill({ level }: { level: Level }) {
  return (
    <span className="inline-flex rounded-full px-3 py-1 text-sm font-medium text-[#102017]" style={{ background: LEVEL_COLOR[level] }}>
      {LEVEL_LABEL[level]}
    </span>
  );
}
