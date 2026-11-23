"use client";

import { useEffect, useRef, useState } from "react";
import { evaluate, getScenario, listScenarios, openMeteo, routeWeek } from "@/lib/api";
import type { RouteWeek, ScenarioDetail, ScenarioMeta, Snapshot, ZoneScore } from "@/lib/types";
import { TOWNS } from "@/lib/towns";
import { Atlas } from "./Atlas";

const DEFAULT_SCENARIO = "pico_cuenca_alta";

const EMPTY_SNAPSHOT: Snapshot = {
  rain_acc_mm: 8,
  intensity_mm_h: 3,
  burst_mm_30min: 0,
  soil_moisture: 0.38,
  data_age_min: 5,
  sensor_quality: 0.95,
};

type Reading = { narrative: string; zones: ZoneScore[]; note?: string };

async function fetchInitial() {
  const listed = await listScenarios();
  const detail = await getScenario(DEFAULT_SCENARIO);
  return { listed, detail };
}

export function Dashboard() {
  const [catalog, setCatalog] = useState<ScenarioMeta[]>([]);
  const [scenario, setScenario] = useState<ScenarioDetail | null>(null);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selectedId, setSelectedId] = useState("cuenca_alta");
  const [mode, setMode] = useState<"scenario" | "manual" | "meteo" | "ruta">("scenario");
  const [manual, setManual] = useState<Reading | null>(null);
  const [knobs, setKnobs] = useState<Snapshot>(EMPTY_SNAPSHOT);
  const [route, setRoute] = useState<RouteWeek | null>(null);
  const [townName, setTownName] = useState<string>(TOWNS[0].name);
  const [routeBusy, setRouteBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(true);
  const [meteoBusy, setMeteoBusy] = useState(false);
  const latestRequest = useRef(0);
  const readings = useRef(new Map<string, RouteWeek>());

  function connected({ listed, detail }: Awaited<ReturnType<typeof fetchInitial>>) {
    setCatalog(listed.scenarios);
    setScenario(detail);
    setFrameIndex(0);
    setError(null);
    setConnecting(false);
  }

  function disconnected() {
    setError("El motor de Python no está corriendo en el puerto 8000.");
    setConnecting(false);
  }

  const stayOnDemo = useRef(false);

  useEffect(() => {
    let cancelled = false;
    fetchInitial().then(
      (data) => {
        if (!cancelled) connected(data);
      },
      () => {
        if (!cancelled) disconnected();
      },
    );
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

  const frameCount = scenario?.frames.length ?? 0;

  function backToScenario() {
    latestRequest.current += 1;
    setMode("scenario");
  }

  function togglePlay() {
    if (!scenario) return;
    backToScenario();
    if (playing) {
      setPlaying(false);
      return;
    }
    if (mode === "scenario" && frameIndex >= frameCount - 1) setFrameIndex(0);
    setPlaying(true);
  }

  function goToFrame(index: number) {
    if (!scenario) return;
    backToScenario();
    setPlaying(false);
    setFrameIndex(Math.max(0, Math.min(frameCount - 1, index)));
  }

  useEffect(() => {
    function onKey(event: globalThis.KeyboardEvent) {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest("button, input, select, textarea, a, summary, [role=button]")) return;
      if (mode === "ruta" && (event.key === "ArrowRight" || event.key === "ArrowLeft")) {
        event.preventDefault();
        if (routeBusy) return;
        const index = TOWNS.findIndex((town) => town.name === townName);
        const next = TOWNS[event.key === "ArrowRight" ? index + 1 : index - 1];
        if (next) pullRoute(next);
        return;
      }
      if (event.key === " ") {
        if (mode === "ruta") return;
        event.preventDefault();
        togglePlay();
      } else if (event.key === "ArrowRight") {
        event.preventDefault();
        goToFrame(mode === "scenario" ? frameIndex + 1 : frameIndex);
      } else if (event.key === "ArrowLeft") {
        event.preventDefault();
        goToFrame(mode === "scenario" ? frameIndex - 1 : frameIndex);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  const frame = mode === "scenario" ? scenario?.frames[frameIndex] : null;
  const zones = mode === "scenario" || mode === "ruta" ? (scenario?.frames[frameIndex]?.zones ?? []) : (manual?.zones ?? []);
  const narrative = mode === "ruta" ? (route?.headline ?? "") : mode === "scenario" ? (frame?.narrative ?? "") : (manual?.narrative ?? "");
  const selected = zones.find((zone) => zone.zone_id === selectedId) ?? zones[0];

  function retry() {
    setConnecting(true);
    fetchInitial().then(connected, disconnected);
  }

  async function chooseScenario(id: string) {
    stayOnDemo.current = true;
    setPlaying(false);
    const request = ++latestRequest.current;
    try {
      const detail = await getScenario(id);
      if (request !== latestRequest.current) return;
      setScenario(detail);
      setFrameIndex(0);
      setMode("scenario");
      setManual(null);
      setError(null);
    } catch {
      if (request === latestRequest.current) setError("No se pudo cargar el escenario.");
    }
  }

  async function runKnobs(next: Snapshot) {
    stayOnDemo.current = true;
    setKnobs(next);
    setPlaying(false);
    const request = ++latestRequest.current;
    try {
      const result = await evaluate(next);
      if (request !== latestRequest.current) return;
      setManual(result);
      setMode("manual");
      setError(null);
    } catch {
      if (request === latestRequest.current) setError("El motor no respondió al mover las perillas.");
    }
  }

  async function pullMeteo() {
    stayOnDemo.current = true;
    setPlaying(false);
    setMeteoBusy(true);
    const request = ++latestRequest.current;
    try {
      const result = await openMeteo();
      if (request !== latestRequest.current) return;
      setManual({ narrative: result.narrative, zones: result.zones, note: result.disclaimer });
      setKnobs(result.snapshot);
      setMode("meteo");
      setError(null);
    } catch {
      if (request === latestRequest.current) setError("Open-Meteo no respondió. Los escenarios locales siguen disponibles.");
    } finally {
      setMeteoBusy(false);
    }
  }

  async function pullRoute(town: { name: string; lat: number; lon: number }) {
    setPlaying(false);
    setTownName(town.name);
    const cached = readings.current.get(town.name);
    if (cached) {
      setRoute(cached);
      if (!stayOnDemo.current) setMode("ruta");
      setRouteBusy(false);
      return;
    }
    setRouteBusy(true);
    const request = ++latestRequest.current;
    try {
      const reading = await routeWeek(town.lat, town.lon, town.name);
      if (request !== latestRequest.current) return;
      readings.current.set(town.name, reading);
      setRoute(reading);
      if (!stayOnDemo.current) setMode("ruta");
      setError(null);
    } catch {
      if (request === latestRequest.current) setError("La lectura real de la RN9 no respondió. El escenario simulado sigue disponible.");
    } finally {
      if (request === latestRequest.current) setRouteBusy(false);
    }
  }

  useEffect(() => {
    pullRoute(TOWNS[0]);
  }, []);

  return <Atlas catalog={catalog} scenario={scenario} frameIndex={frameIndex} playing={playing}
    mode={mode} zones={zones} selected={selected} narrative={narrative} knobs={knobs}
    note={mode !== "scenario" && mode !== "ruta" ? manual?.note : undefined} error={error} connecting={connecting} meteoBusy={meteoBusy}
    route={route} routeBusy={routeBusy} townName={townName}
    choose={chooseScenario} select={setSelectedId} step={goToFrame} toggle={togglePlay}
    evaluate={runKnobs} meteo={pullMeteo} retry={retry}     pickTown={name => {
      stayOnDemo.current = false;
      setMode("ruta");
      const town = TOWNS.find(item => item.name === name);
      if (town) pullRoute(town);
    }}/>;
}
