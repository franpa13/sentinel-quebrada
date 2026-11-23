"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { getTrip, listPueblos } from "@/lib/api";
import { BAND_COLOR, type Pueblo, type RouteBand, type Traza, type Trip as TripReading } from "@/lib/types";
import { RouteMap } from "./RouteMap";

const HOME = "Volcán";
const MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const KIND_LABEL: Record<string, string> = { alud: "Alud", crecida: "Crecida", barro: "Barro" };

/** Cómo se dice cada nivel del motor a quien va a viajar. El nivel lo decide el motor. */
const RISK: Record<RouteBand, { short: string; headline: string; advice: string; icon: "ok" | "info" | "warn" | "stop" }> = {
  baja: {
    short: "Poco probable",
    headline: "Es poco probable que la lluvia corte la ruta",
    advice: "Se espera poca lluvia en el camino. Igual, una tormenta fuerte de tarde puede tapar un badén.",
    icon: "ok",
  },
  atencion: {
    short: "Poco probable, confirmá",
    headline: "No vemos señales de corte, pero confirmá antes de salir",
    advice: "Se espera poca lluvia en el camino. Nuestro pronóstico es aproximado y no ve tormentas cortas, y la Ruta 9 es la única salida de la Quebrada: revisá el estado de la ruta el mismo día.",
    icon: "info",
  },
  media: {
    short: "Posible",
    headline: "La ruta podría cortarse en algún tramo",
    advice: "Se espera lluvia suficiente para que algún arroyo cruce la ruta con agua o barro. Si viajás, salí temprano, con tiempo de sobra, y revisá el estado de la ruta.",
    icon: "warn",
  },
  alta: {
    short: "Probable",
    headline: "Es probable que la lluvia corte la ruta",
    advice: "La lluvia prevista se parece a la de días en que la ruta se cortó. Si podés, cambiá el día del viaje.",
    icon: "warn",
  },
  muy_alta: {
    short: "Muy probable",
    headline: "Es muy probable que la lluvia corte la ruta",
    advice: "La lluvia prevista se parece a la de días en que la ruta se cortó. Si podés, cambiá el día del viaje y seguí el parte oficial.",
    icon: "stop",
  },
};

const TIPS = [
  "Revisá el estado de la Ruta 9 en Vialidad Nacional o en Defensa Civil de Jujuy el mismo día del viaje.",
  "Si ves agua o barro corriendo sobre la ruta, no cruces: esperá a que baje.",
  "Llevá agua, abrigo y el celular cargado. Si la ruta se corta, reabrirla puede llevar horas o días.",
  "Contale a alguien por dónde vas y a qué hora pensás llegar.",
];

function Icon({ kind }: { kind: "ok" | "info" | "warn" | "stop" }) {
  return <svg viewBox="0 0 24 24" aria-hidden="true" className="risk-icon">
    {kind === "ok" && <><circle cx="12" cy="12" r="11" /><path d="m7 12.5 3.2 3.2L17 9" /></>}
    {kind === "info" && <><circle cx="12" cy="12" r="11" /><path d="M12 11v6M12 7.2v.1" /></>}
    {kind === "warn" && <><path d="M12 1.8 23 21.5H1Z" /><path d="M12 9v5.5M12 17.6v.1" /></>}
    {kind === "stop" && <><path d="M7.4 1h9.2L23 7.4v9.2L16.6 23H7.4L1 16.6V7.4Z" /><path d="m8.5 8.5 7 7m0-7-7 7" /></>}
  </svg>;
}

function dayParts(date: string) {
  const day = new Date(`${date}T12:00:00`);
  const today = new Date();
  const tomorrow = new Date(today.getTime() + 86400000);
  const same = (a: Date, b: Date) => a.toDateString() === b.toDateString();
  const long = day.toLocaleDateString("es-AR", { weekday: "long", day: "numeric", month: "long" });
  return {
    weekday: same(day, today) ? "Hoy" : same(day, tomorrow) ? "Mañana" : day.toLocaleDateString("es-AR", { weekday: "short" }).replace(".", ""),
    number: day.getDate(),
    long: same(day, today) ? `hoy, ${long}` : same(day, tomorrow) ? `mañana, ${long}` : long,
  };
}

function fmt(value: number | null | undefined, digits = 1) {
  return value == null ? "—" : value.toLocaleString("es-AR", { maximumFractionDigits: digits });
}

function rainText(mm: number | null | undefined) {
  if (mm == null) return "sin dato de lluvia";
  if (mm < 0.5) return "casi sin lluvia";
  return `${fmt(mm)} mm de lluvia`;
}

function listWords(words: string[]) {
  return words.length < 2 ? words.join("") : `${words.slice(0, -1).join(", ")} y ${words[words.length - 1]}`;
}

function readQuery(names: string[]) {
  const query = new URLSearchParams(window.location.search);
  const pick = (key: string) => {
    const value = query.get(key);
    return value && names.includes(value) ? value : HOME;
  };
  return { desde: pick("desde"), hasta: pick("hasta"), dia: query.get("dia") };
}

function setQuery(key: string, value: string | null) {
  const query = new URLSearchParams(window.location.search);
  if (value === null) query.delete(key);
  else query.set(key, value);
  window.history.replaceState(null, "", `?${query}`);
}

export function Trip() {
  const [pueblos, setPueblos] = useState<Pueblo[]>([]);
  const [traza, setTraza] = useState<Traza | null>(null);
  const [desde, setDesde] = useState(HOME);
  const [hasta, setHasta] = useState(HOME);
  const [trip, setTrip] = useState<TripReading | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [day, setDay] = useState<string | null>(null);
  const [openTown, setOpenTown] = useState<string | null>(null);
  const [month, setMonth] = useState<number | null>(null);
  const [allCuts, setAllCuts] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const pending = useRef<AbortController | null>(null);

  const answerRef = useRef<HTMLElement | null>(null);

  function pickDay(date: string | null, reveal = false) {
    setDay(date);
    setQuery("dia", date);
    if (reveal && date) {
      const smooth = !window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      window.requestAnimationFrame(() => answerRef.current?.scrollIntoView({ behavior: smooth ? "smooth" : "auto", block: "start" }));
    }
  }

  function load(from: string, to: string, wanted?: string | null) {
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    setDesde(from);
    setHasta(to);
    setBusy(true);
    setError(null);
    setQuery("desde", from);
    setQuery("hasta", to);
    getTrip(from, to, controller.signal).then(
      (reading) => {
        if (controller.signal.aborted) return;
        setTrip(reading);
        setDay((current) => {
          const keep = wanted ?? current;
          const next = keep && reading.days.some((item) => item.date === keep) ? keep : null;
          setQuery("dia", next);
          return next;
        });
        setOpenTown(null);
        setBusy(false);
      },
      () => {
        if (controller.signal.aborted) return;
        setError("No pudimos consultar el pronóstico. Probá de nuevo en un momento.");
        setBusy(false);
      },
    );
  }

  useEffect(() => () => pending.current?.abort(), []);

  useEffect(() => {
    let cancelled = false;
    listPueblos().then(
      ({ pueblos: list, traza: line }) => {
        if (cancelled) return;
        const start = readQuery(list.map((item) => item.name));
        setPueblos(list);
        setTraza(line);
        load(start.desde, start.hasta, start.dia);
      },
      () => {
        if (cancelled) return;
        setError("El servicio no está disponible. Si sos quien lo administra: el motor de Python no está corriendo en el puerto 8000.");
        setBusy(false);
      },
    );
    return () => {
      cancelled = true;
    };
  }, [attempt]);

  function retry() {
    if (pueblos.length) load(desde, hasta);
    else {
      setBusy(true);
      setError(null);
      setAttempt((n) => n + 1);
    }
  }

  const selected = trip?.days.find((item) => item.date === day) ?? null;
  const best = trip?.days.find((item) => item.date === trip.best_day) ?? null;
  const fromIndex = pueblos.findIndex((item) => item.name === desde);
  const toIndex = pueblos.findIndex((item) => item.name === hasta);
  const [low, high] = [Math.min(fromIndex, toIndex), Math.max(fromIndex, toIndex)];
  const stops = high - low + 1;
  const tripName = desde === hasta ? `en ${desde}` : `de ${desde} a ${hasta}`;

  const byMonth = useMemo(() => {
    const counts = Array.from({ length: 12 }, () => new Set<string>());
    for (const cut of trip?.cortes ?? []) counts[Number(cut.date.slice(5, 7)) - 1].add(cut.episode);
    return counts.map((set) => set.size);
  }, [trip]);
  const episodes = byMonth.reduce((sum, count) => sum + count, 0);
  const topMonths = byMonth.map((count, index) => ({ count, index }))
    .filter((item) => item.count > 0).sort((a, b) => b.count - a.count || a.index - b.index).slice(0, 3)
    .sort((a, b) => a.index - b.index).map((item) => MONTHS[item.index]);
  const maxMonth = Math.max(1, ...byMonth);
  const thisMonth = new Date().getMonth();
  const filtered = (trip?.cortes ?? []).filter((cut) => month === null || Number(cut.date.slice(5, 7)) - 1 === month);
  const cuts = allCuts || month !== null ? filtered : filtered.slice(0, 4);

  const colors = useMemo(() => {
    const out: Record<string, string> = {};
    for (const town of selected?.towns ?? []) out[town.name] = BAND_COLOR[town.operational];
    return out;
  }, [selected]);

  const band = selected?.operational ?? trip?.operational ?? "atencion";
  const risk = RISK[band];

  return <main className="sheet trip">
    <div className="trip-flow">
    <section className="ask">
      <p className="eyebrow">Ruta Nacional 9 · Quebrada de Humahuaca, Jujuy</p>
      <h1>¿Se corta la ruta?</h1>
      <p className="lead">Elegí tu viaje y te decimos qué tan probable es que la lluvia corte la Ruta 9 en los próximos 7 días.</p>

      <form className="planner" onSubmit={(event) => event.preventDefault()} aria-label="Tu viaje">
        <label><span>Salgo de</span>
          <select value={desde} disabled={!pueblos.length} onChange={(event) => load(event.target.value, hasta)}>
            {pueblos.map((item) => <option key={item.name}>{item.name}</option>)}
          </select>
        </label>
        <button type="button" className="swap" title="Invertir el viaje" aria-label="Invertir salida y llegada" disabled={!pueblos.length || desde === hasta}
          onClick={() => load(hasta, desde)}>⇄</button>
        <label><span>Voy a</span>
          <select value={hasta} disabled={!pueblos.length} onChange={(event) => load(desde, event.target.value)}>
            {pueblos.map((item) => <option key={item.name}>{item.name}</option>)}
          </select>
        </label>
      </form>

      <p className="hint">{desde === hasta ? "Tocá un pueblo en el mapa o elegilo arriba para decir a dónde vas." : `Tu viaje pasa por ${stops} pueblos. Si la ruta se corta en cualquiera de ellos, el viaje se complica.`}</p>
    </section>

    <section className="ask-day">
      <fieldset className="when-ask">
        <legend>¿Qué día viajás?</legend>
        <div className="date-chips">
          {trip && trip.days.length > 0 ? trip.days.map((item) => {
            const parts = dayParts(item.date);
            return <button key={item.date} type="button" aria-pressed={item.date === day} onClick={() => pickDay(item.date, true)}>
              <span>{parts.weekday}</span><b>{parts.number}</b>
            </button>;
          }) : Array.from({ length: 7 }, (_, index) => <span key={index} className="chip-skeleton" />)}
        </div>
        {trip && !trip.days.length && !busy && <p className="hint">No conseguimos el pronóstico de esta semana. Sin ese dato no podemos decir que la ruta está libre.</p>}
      </fieldset>
    </section>

    {error && <div className="error" role="alert">{error} <button onClick={retry} disabled={busy}>Reintentar</button></div>}

    <section ref={answerRef} className={selected ? "answer" : "answer waiting"} aria-live="polite" aria-busy={busy} style={{ ["--tone" as string]: selected ? BAND_COLOR[band] : "#9aabae" }}>
      {!trip || !selected ? <p className="loading">{busy && !trip ? `Consultando el pronóstico de lluvia en ${stops > 0 ? stops : 1} pueblo(s)…` : trip && trip.days.length ? "↑ Elegí qué día viajás y te decimos si la ruta puede cortarse." : "Sin pronóstico por ahora."}</p> : <>
        <Icon kind={risk.icon} />
        <div>
          <p className="when">Viajando {tripName}, {dayParts(selected.date).long}</p>
          <h2>{risk.headline}</h2>
          <p>{risk.advice}</p>
          <p className="facts">
            {selected.driver && stops > 1 && <span>Lugar a mirar: <b>{selected.driver}</b></span>}
            <span>Lluvia: <b>{rainText(selected.max_rain_mm)}</b></span>
          </p>
          {best && best.date !== selected.date && <button type="button" className="to-best" onClick={() => pickDay(best.date)}>
            Ver el mejor día de la semana: {dayParts(best.date).long} →
          </button>}
          {busy && <p className="updating" role="status">Actualizando…</p>}
        </div>
      </>}
    </section>

    {trip && selected && <section className="week" aria-label="Los próximos 7 días">
      <h2>¿Podés cambiar el día?</h2>
      <p className="muted">Así viene el resto de la semana para este viaje. Tocá un día para verlo.</p>
      <div className="week-days">
        {trip.days.map((item) => {
          const parts = dayParts(item.date);
          const itemRisk = RISK[item.operational];
          return <button key={item.date} type="button" className="day" aria-pressed={item.date === day}
            style={{ ["--tone" as string]: BAND_COLOR[item.operational] }}
            aria-label={`${parts.long}: ${itemRisk.short}${item.date === trip.best_day ? ", el mejor día" : ""}`}
            onClick={() => pickDay(item.date)}>
            {item.date === trip.best_day && <span className="best">Mejor día</span>}
            <span className="weekday">{parts.weekday} <b>{parts.number}</b></span>
            <Icon kind={itemRisk.icon} />
            <span className="day-risk">{itemRisk.short}</span>
            <small>{item.max_rain_mm == null ? "sin dato" : `${fmt(item.max_rain_mm)} mm`}</small>
          </button>;
        })}
      </div>
      <p className="legend">
        {(["baja", "atencion", "media", "alta", "muy_alta"] as RouteBand[]).map((key) => <span key={key} style={{ ["--tone" as string]: BAND_COLOR[key] }}><Icon kind={RISK[key].icon} />{RISK[key].short}</span>)}
        <span>mm = milímetros de lluvia esperados en el día</span>
      </p>
    </section>}

    <section className="tips">
      <h2>Antes de salir</h2>
      <ul>{TIPS.map((tip) => <li key={tip}>{tip}</li>)}</ul>
    </section>

    {trip && selected && <details className="more">
      <summary>¿Por qué decimos esto? <small>Detalle pueblo por pueblo</small></summary>
      <p className="muted">Miramos la lluvia pronosticada en cada pueblo del viaje, el terreno y los cortes que ya pasaron cerca. El pueblo más complicado del día define el resultado del viaje.</p>
      <ul className="towns">{selected.towns.map((town) => {
        const reading = trip.towns.find((item) => item.place.name === town.name);
        const detail = reading?.days.find((item) => item.date === selected.date);
        const open = openTown === town.name;
        return <li key={town.name}>
          <button type="button" aria-expanded={open} onClick={() => setOpenTown(open ? null : town.name)} style={{ ["--tone" as string]: BAND_COLOR[town.operational] }}>
            <i className="dot" />
            <span className="town-name">{town.name}</span>
            <span className="town-risk">{RISK[town.operational].short}</span>
            <span className="town-rain">{rainText(town.rain_mm)}</span>
            <span className="chev" aria-hidden="true">{open ? "−" : "+"}</span>
          </button>
          {open && reading && <div className="town-detail">
            {detail?.note && <p className="notice">{detail.note}</p>}
            <p>Puntaje de corte: <b>{fmt(detail?.chance)} de 100</b>. Se arma así:</p>
            {detail && detail.factors.length > 0 && <ul className="factor-list">{detail.factors.map((factor) => <li key={factor.id}>
              <span>{factor.label}</span><b>+{fmt(factor.points)}</b><p>{factor.detail}</p>
            </li>)}</ul>}
            <p className="muted">{reading.aluvional.terrain.note} {reading.aluvional.soil.note}</p>
          </div>}
        </li>;
      })}</ul>
      <p className="muted">Resumen del motor: {trip.headline}</p>
    </details>}

    {trip && <details className="more">
      <summary>¿Se cortó antes este camino? <small>{episodes ? `${episodes} veces que salieron en las noticias` : "Sin cortes publicados"}</small></summary>
      {episodes > 0 && <p className="muted">
        Juntamos {episodes} episodios de corte publicados en diarios cerca de tu recorrido.
        {topMonths.length > 0 && ` La mayoría fueron en ${listWords(topMonths)}, en temporada de lluvias.`}
        {" "}Tocá un mes para ver solo esos.
      </p>}
      <div className="months" role="group" aria-label="Cortes por mes">
        {byMonth.map((count, index) => <button key={index} type="button" aria-pressed={month === index}
          className={index === thisMonth ? "now" : undefined}
          aria-label={`${MONTHS[index]}: ${count} corte(s)${index === thisMonth ? ", este mes" : ""}`}
          onClick={() => setMonth(month === index ? null : index)}>
          <span className="col"><i style={{ height: `${(count / maxMonth) * 100}%` }} /></span>
          <b>{count || ""}</b><small>{MONTHS[index].slice(0, 3)}</small>
        </button>)}
      </div>
      <ol className="cuts">
        {cuts.map((cut) => <li key={`${cut.episode}-${cut.place}`}>
          <span className={`kind ${cut.kind}`}>{KIND_LABEL[cut.kind] ?? cut.kind}</span>
          <div><b>{new Date(`${cut.date}T12:00:00`).toLocaleDateString("es-AR", { day: "numeric", month: "long", year: "numeric" })} · {cut.place}</b>
            <p>{cut.summary} <a href={cut.url} target="_blank" rel="noreferrer">Ver nota ({cut.source})</a></p></div>
        </li>)}
        {!cuts.length && <li className="muted">No hay cortes publicados en {month === null ? "este camino" : MONTHS[month]}.</li>}
      </ol>
      {!allCuts && month === null && filtered.length > cuts.length && <button type="button" className="link" onClick={() => setAllCuts(true)}>Ver los {filtered.length} cortes</button>}
    </details>}

    {trip && <details className="more">
      <summary>Qué no es esta página</summary>
      <ul className="limits">{trip.limits.map((limit) => <li key={limit}>{limit}</li>)}</ul>
    </details>}
    </div>

    <aside className="trip-map">
      <RouteMap pueblos={pueblos} traza={traza} desde={desde} hasta={hasta} colors={colors} cuts={trip?.cortes ?? []}
        onPick={(name) => load(desde, name)} />
    </aside>
  </main>;
}
