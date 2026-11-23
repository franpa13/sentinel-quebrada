"use client";

import { useState } from "react";
import { Dashboard } from "./Dashboard";
import { Trip } from "./Trip";

export type View = "viaje" | "cuenca";

const FOOTER: Record<View, string> = {
  viaje: "Estimamos con la lluvia pronosticada y con cortes que salieron en diarios. No es el parte oficial de Vialidad Nacional ni una orden de cancelar el viaje.",
  cuenca: "Esquema de simulación. No es cartografía oficial ni una orden de evacuación. Kirpich estima el tiempo de concentración, no la llegada de una colada.",
};

export function Shell({ initial }: { initial: View }) {
  const [view, setView] = useState<View>(initial);

  function go(next: View) {
    setView(next);
    const query = new URLSearchParams(window.location.search);
    if (next === "cuenca") query.set("vista", "cuenca");
    else query.delete("vista");
    const text = query.toString();
    window.history.replaceState(null, "", text ? `?${text}` : window.location.pathname);
  }

  return <div className="atlas">
    <header className="mast">
      <div className="brand">
        <svg viewBox="0 0 46 37" aria-hidden="true"><path d="M2 31 17 5l8 13 5-8 14 21H2Zm9-5 6-10 7 11m1-9 5 8" fill="none" stroke="currentColor" strokeWidth="2.8" strokeLinejoin="round"/></svg>
        Sentinel Quebrada
      </div>
      <nav className="views" aria-label="Vistas">
        <button type="button" aria-current={view === "viaje" ? "page" : undefined} onClick={() => go("viaje")}>¿Se corta la ruta?</button>
        <button type="button" aria-current={view === "cuenca" ? "page" : undefined} onClick={() => go("cuenca")}>Simulación técnica</button>
      </nav>
    </header>
    {view === "viaje" ? <Trip /> : <Dashboard />}
    <footer>{FOOTER[view]}</footer>
  </div>;
}
