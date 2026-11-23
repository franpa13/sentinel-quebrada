"use client";

import "leaflet/dist/leaflet.css";
import { useEffect, useRef, useState } from "react";
import type * as Leaflet from "leaflet";
import type { Cut, Pueblo, Traza } from "@/lib/types";

type Props = {
  pueblos: Pueblo[];
  traza: Traza | null;
  desde: string;
  hasta: string;
  colors: Record<string, string | undefined>;
  cuts: Cut[];
  onPick: (name: string) => void;
};

const ROUTE_INK = "#173744";
const KIND_LABEL: Record<string, string> = { alud: "Alud", crecida: "Crecida", barro: "Barro" };

function escapeHtml(text: string) {
  return text.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char] ?? char);
}

function segment(traza: Traza, fromKm: number, toKm: number): [number, number][] {
  const [low, high] = [Math.min(fromKm, toKm), Math.max(fromKm, toKm)];
  return traza.coordinates.filter((_, index) => traza.km[index] >= low - 0.01 && traza.km[index] <= high + 0.01);
}

export function RouteMap({ pueblos, traza, desde, hasta, colors, cuts, onPick }: Props) {
  const box = useRef<HTMLDivElement | null>(null);
  const lib = useRef<typeof Leaflet | null>(null);
  const map = useRef<Leaflet.Map | null>(null);
  const layer = useRef<Leaflet.LayerGroup | null>(null);
  const pick = useRef(onPick);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    pick.current = onPick;
  }, [onPick]);

  useEffect(() => {
    let cancelled = false;
    import("leaflet").then((L) => {
      if (cancelled || !box.current || map.current) return;
      lib.current = L;
      const created = L.map(box.current, { zoomControl: true, scrollWheelZoom: false, dragging: !L.Browser.mobile, attributionControl: true });
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 17,
        attribution: '© <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap</a>',
      }).addTo(created);
      created.setView([-23.56, -65.41], 9);
      layer.current = L.layerGroup().addTo(created);
      map.current = created;
      setReady(true);
    });
    return () => {
      cancelled = true;
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Encuadre: solo cuando cambia el viaje, no cuando cambia el día.
  useEffect(() => {
    const L = lib.current;
    if (!ready || !L || !map.current || !traza || !pueblos.length) return;
    const from = pueblos.find((item) => item.name === desde);
    const to = pueblos.find((item) => item.name === hasta);
    if (!from || !to) return;
    if (from.name === to.name) {
      map.current.setView([from.lat, from.lon], 12);
      return;
    }
    const points = [...segment(traza, from.route_km, to.route_km), [from.lat, from.lon], [to.lat, to.lon]] as [number, number][];
    map.current.fitBounds(L.latLngBounds(points), { padding: [36, 36], maxZoom: 13 });
  }, [ready, traza, pueblos, desde, hasta]);

  useEffect(() => {
    const L = lib.current;
    const group = layer.current;
    if (!ready || !L || !group || !traza) return;
    group.clearLayers();
    const from = pueblos.find((item) => item.name === desde);
    const to = pueblos.find((item) => item.name === hasta);
    const [low, high] = from && to ? [Math.min(from.route_km, to.route_km), Math.max(from.route_km, to.route_km)] : [0, 0];

    L.polyline(traza.coordinates, { color: "#ffffff", weight: 8, opacity: 0.9 }).addTo(group);
    L.polyline(traza.coordinates, { color: "#7c9296", weight: 4, opacity: 0.9 }).addTo(group);
    if (from && to && from.name !== to.name) {
      const part = segment(traza, from.route_km, to.route_km);
      L.polyline(part, { color: "#ffffff", weight: 11, opacity: 0.95 }).addTo(group);
      L.polyline(part, { color: ROUTE_INK, weight: 6 }).addTo(group);
    }

    const places = new Map<string, Cut[]>();
    for (const cut of cuts) {
      const key = `${cut.lat},${cut.lon}`;
      places.set(key, [...(places.get(key) ?? []), cut]);
    }
    for (const group_cuts of places.values()) {
      const first = group_cuts[0];
      const html = `<div class="map-pop"><b>Cortes publicados acá</b>${group_cuts
        .map((cut) => `<p><span>${escapeHtml(cut.date.slice(0, 4))} · ${escapeHtml(KIND_LABEL[cut.kind] ?? cut.kind)}</span> ${escapeHtml(cut.place)}</p>`)
        .join("")}</div>`;
      L.circleMarker([first.lat, first.lon], { radius: 5 + Math.min(group_cuts.length, 4), color: "#ffffff", weight: 1.5, fillColor: "#b0573a", fillOpacity: 0.9 })
        .bindPopup(html, { maxWidth: 260 })
        .bindTooltip(`${group_cuts.length} corte(s) publicado(s)`, { direction: "top" })
        .addTo(group);
    }

    for (const pueblo of pueblos) {
      const inTrip = pueblo.route_km >= low - 0.01 && pueblo.route_km <= high + 0.01;
      const color = inTrip ? colors[pueblo.name] ?? ROUTE_INK : "#9aabae";
      if (pueblo.off_route_km > 0.5) {
        L.polyline([[pueblo.lat, pueblo.lon], pueblo.route_point], { color, weight: 3, dashArray: "4 5", opacity: 0.9 }).addTo(group);
      }
      const role = pueblo.name === desde ? " · salida" : pueblo.name === hasta ? " · llegada" : "";
      const marker = L.circleMarker([pueblo.lat, pueblo.lon], {
        radius: pueblo.name === desde || pueblo.name === hasta ? 10 : 8,
        color: "#ffffff",
        weight: 3,
        fillColor: color,
        fillOpacity: 1,
      });
      marker.bindTooltip(`${escapeHtml(pueblo.name)}${role}`, {
        permanent: true,
        direction: "right",
        offset: [10, 0],
        className: `town-label${inTrip ? "" : " off"}`,
      });
      marker.on("click", () => pick.current(pueblo.name));
      marker.addTo(group);
    }
  }, [ready, traza, pueblos, desde, hasta, colors, cuts]);

  return <figure className="route-map">
    <div ref={box} className="route-map-canvas" role="img" aria-label={`Mapa de la Ruta 9 de ${desde} a ${hasta}`} />
    <figcaption>
      <span><i className="k-route" />Tu viaje</span>
      <span><i className="k-town" />Pueblo (color del día elegido)</span>
      <span><i className="k-cut" />Cortes publicados</span>
      <small>Tocá un pueblo para elegirlo como llegada. Traza de OpenStreetMap; no es cartografía oficial de Vialidad.</small>
    </figcaption>
  </figure>;
}
