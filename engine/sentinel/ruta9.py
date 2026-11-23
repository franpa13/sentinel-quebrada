"""Chance de que la lluvia corte la RN9 en la Quebrada.

El catálogo son cortes publicados, con fuente. No es el parte de Vialidad.
La chance no es una probabilidad estadística: es un puntaje con tres factores.
La historia del lugar y la temporada solo amplifican la lluvia de esta semana.
Una semana en cero no hereda un corte viejo.
"""

from __future__ import annotations

import datetime

from sentinel.lugar import distance_m

CORRIDOR_KM = 25.0
HISTORY_KM = 15.0
# Lluvia 55, historia 35, temporada 20. Tope 100.
RAIN_WEIGHT = 55.0
HISTORY_CAP = 35.0
SEASON_CAP = 20.0
# Peor a la derecha. Atención está arriba de baja: un dato que falta no es calma.
OPERATIONAL_RANK = {"baja": 0, "atencion": 1, "media": 2, "alta": 3, "muy_alta": 4}

# De sur a norte, en el orden en que los cruza quien sale de Volcán.
PUEBLOS: tuple[dict, ...] = (
    {"name": "Volcán", "lat": -23.919, "lon": -65.463},
    {"name": "Tumbaya", "lat": -23.857, "lon": -65.467},
    {"name": "Purmamarca", "lat": -23.746, "lon": -65.499},
    {"name": "Maimará", "lat": -23.624, "lon": -65.408},
    {"name": "Tilcara", "lat": -23.577, "lon": -65.393},
    {"name": "Huacalera", "lat": -23.436, "lon": -65.351},
    {"name": "Uquía", "lat": -23.309, "lon": -65.356},
    {"name": "Humahuaca", "lat": -23.205, "lon": -65.348},
)

CORTES: tuple[dict, ...] = (
    {
        "episode": "2012-12-11-volcan",
        "date": "2012-12-11",
        "place": "Volcán, Quebrada de los Filtros",
        "lat": -23.919,
        "lon": -65.463,
        "kind": "alud",
        "summary": "Alud de la Quebrada de los Filtros. Unos 400 m de RN9 tapados. Seis camiones quedaron en el predio de la calera. A media mañana, paso con precaución.",
        "source": "El Ancasti",
        "url": "https://www.elancasti.com.ar/nacionales/2012/12/11/alud-volcn-cort-ruta-afect-predio-fbrica-194760.html",
    },
    {
        "episode": "2017-01-10-volcan",
        "date": "2017-01-10",
        "place": "Volcán",
        "lat": -23.919,
        "lon": -65.463,
        "kind": "alud",
        "summary": "Alud de barro y piedra sobre Volcán. La RN9 quedó cortada varios días. El paso se anunció habilitado el 20 de enero, con precaución en Volcán, Bárcena y Tumbaya.",
        "source": "Diario de Cuyo / Gobierno de Jujuy",
        "url": "https://www.diariodecuyo.com.ar/argentina/Tras-el-alud-que-borro-casi-todo-un-pueblo-Jujuy-sigue-en-alerta-20170113-0012.html",
    },
    {
        "episode": "2017-01-10-volcan",
        "date": "2017-01-10",
        "place": "Bárcena",
        "lat": -23.966,
        "lon": -65.448,
        "kind": "alud",
        "summary": "Mismo episodio del 10 de enero. Bárcena quedó en la traza cortada entre el pueblo y San Salvador.",
        "source": "Diario de Cuyo",
        "url": "https://www.diariodecuyo.com.ar/argentina/Tras-el-alud-que-borro-casi-todo-un-pueblo-Jujuy-sigue-en-alerta-20170113-0012.html",
    },
    {
        "episode": "2017-01-10-volcan",
        "date": "2017-01-10",
        "place": "Tumbaya",
        "lat": -23.857,
        "lon": -65.467,
        "kind": "alud",
        "summary": "Mismo episodio. Tumbaya quedó aislada al norte del corte de Volcán.",
        "source": "Diario de Cuyo",
        "url": "https://www.diariodecuyo.com.ar/argentina/Tras-el-alud-que-borro-casi-todo-un-pueblo-Jujuy-sigue-en-alerta-20170113-0012.html",
    },
    {
        "episode": "2017-03-10-tilcara",
        "date": "2017-03-10",
        "place": "Maimará, Arroyo Colorado",
        "lat": -23.624,
        "lon": -65.408,
        "kind": "alud",
        "summary": "Corte antes del acceso sur a Maimará. Hacia el norte solo dejaban llegar hasta Purmamarca.",
        "source": "Todo Jujuy",
        "url": "https://www.todojujuy.com/jujuy/esta-cortada-la-ruta-9-aluviones-n58342",
    },
    {
        "episode": "2017-03-10-tilcara",
        "date": "2017-03-10",
        "place": "Tilcara, 2 km al norte",
        "lat": -23.560,
        "lon": -65.385,
        "kind": "alud",
        "summary": "Segundo corte de esa mañana, dos kilómetros después de Tilcara rumbo a Humahuaca.",
        "source": "Todo Jujuy",
        "url": "https://www.todojujuy.com/jujuy/esta-cortada-la-ruta-9-aluviones-n58342",
    },
    {
        "episode": "2019-01-03-chanarcito",
        "date": "2019-01-03",
        "place": "Chañarcito, Tumbaya Grande",
        "lat": -23.730,
        "lon": -65.490,
        "kind": "alud",
        "summary": "Aluvión de piedras y lodo en Chañarcito. También cortada a la altura de Tumbaya Grande y Molle Punco.",
        "source": "El Tribuno",
        "url": "http://www.eltribuno.com/nota/2019-1-3-10-39-0-por-las-fuertes-tormentas-la-ruta-9-en-jujuy-esta-cortada",
    },
    {
        "episode": "2019-02-01-quebrada",
        "date": "2019-02-01",
        "place": "Tumbaya Grande",
        "lat": -23.857,
        "lon": -65.467,
        "kind": "crecida",
        "summary": "Media calzada en varios badenes de la RN9: Tumbaya Grande, Chañarcito, norte de Tilcara, Trópico y Tunalito.",
        "source": "El Submarino Jujuy",
        "url": "https://elsubmarinojujuy.com.ar/piden-circular-con-precaucion-por-la-ruta-nacional-n9-transito-por-media-calzada/",
    },
    {
        "episode": "2019-02-01-quebrada",
        "date": "2019-02-01",
        "place": "Tilcara, 3 km al norte",
        "lat": -23.555,
        "lon": -65.380,
        "kind": "crecida",
        "summary": "Mismo día. Paso con precaución por la crecida del arroyo Sococha, 3 km al norte de Tilcara.",
        "source": "El Submarino Jujuy",
        "url": "https://elsubmarinojujuy.com.ar/piden-circular-con-precaucion-por-la-ruta-nacional-n9-transito-por-media-calzada/",
    },
    {
        "episode": "2019-02-01-quebrada",
        "date": "2019-02-01",
        "place": "Huacalera, Trópico de Capricornio",
        "lat": -23.440,
        "lon": -65.351,
        "kind": "crecida",
        "summary": "Mismo día. Crecida en el Trópico de Capricornio y en Tunalito, sobre Huacalera.",
        "source": "El Submarino Jujuy",
        "url": "https://elsubmarinojujuy.com.ar/piden-circular-con-precaucion-por-la-ruta-nacional-n9-transito-por-media-calzada/",
    },
    {
        "episode": "2019-11-02-filtros",
        "date": "2019-11-02",
        "place": "Volcán, Quebrada de los Filtros",
        "lat": -23.919,
        "lon": -65.463,
        "kind": "crecida",
        "summary": "Corte total preventivo en los Filtros. En Huichaira, barro y piedra a 2 km al sur de Tilcara. Después, media calzada.",
        "source": "Vía País",
        "url": "https://viapais.com.ar/jujuy/1384063-hubo-cortes-en-la-ruta-9-por-crecidas-en-los-cerros-de-la-quebrada/",
    },
    {
        "episode": "2019-11-02-filtros",
        "date": "2019-11-02",
        "place": "Huichaira",
        "lat": -23.596,
        "lon": -65.401,
        "kind": "barro",
        "summary": "Mismo día. El vado de Huichaira, 2 km al sur de Tilcara, quedó con barro y piedras.",
        "source": "Vía País",
        "url": "https://viapais.com.ar/jujuy/1384063-hubo-cortes-en-la-ruta-9-por-crecidas-en-los-cerros-de-la-quebrada/",
    },
    {
        "episode": "2020-02-17-perchel",
        "date": "2020-02-17",
        "place": "El Perchel",
        "lat": -23.449,
        "lon": -65.352,
        "kind": "crecida",
        "summary": "Corte total en Huichaira, Villa El Perchel y el Trópico de Capricornio. El mayor fue el río Huichaira a la altura de El Perchel.",
        "source": "Vía País",
        "url": "https://viapais.com.ar/jujuy/1592246-la-ruta-9-hacia-la-quebrada-cortada-por-la-crecida-y-desborde-de-arroyos/",
    },
    {
        "episode": "2020-02-17-perchel",
        "date": "2020-02-17",
        "place": "Huichaira",
        "lat": -23.596,
        "lon": -65.401,
        "kind": "crecida",
        "summary": "Mismo día. Huichaira también cortó la traza.",
        "source": "Vía País",
        "url": "https://viapais.com.ar/jujuy/1592246-la-ruta-9-hacia-la-quebrada-cortada-por-la-crecida-y-desborde-de-arroyos/",
    },
    {
        "episode": "2021-01-03-tumbaya",
        "date": "2021-01-03",
        "place": "Tumbaya",
        "lat": -23.857,
        "lon": -65.467,
        "kind": "barro",
        "summary": "Desmoronamientos entre Tumbaya y Purmamarca. Sedimento en Tumbaya, Tunalito y el acceso a Purmamarca. Luego, media calzada.",
        "source": "La Gaceta",
        "url": "https://www.lagaceta.com.ar/nota/875155/actualidad/intensas-lluvias-provocaron-desmoronamientos-cortes-quebrada-humahuaca.html",
    },
    {
        "episode": "2021-01-03-tumbaya",
        "date": "2021-01-03",
        "place": "Purmamarca",
        "lat": -23.746,
        "lon": -65.499,
        "kind": "barro",
        "summary": "Mismo episodio. Acceso a Purmamarca con sedimento sobre la RN9.",
        "source": "La Gaceta",
        "url": "https://www.lagaceta.com.ar/nota/875155/actualidad/intensas-lluvias-provocaron-desmoronamientos-cortes-quebrada-humahuaca.html",
    },
    {
        "episode": "2022-01-17-perchel",
        "date": "2022-01-17",
        "place": "El Perchel, Huacalera",
        "lat": -23.449,
        "lon": -65.352,
        "kind": "crecida",
        "summary": "Corte en El Perchel por canales de riego crecidos. En Volcán, agua y barro de los Filtros sobre la calzada. El día anterior también se había cortado Huichaira.",
        "source": "Pregón",
        "url": "https://www.pregon.com.ar/nota/13556/2022/01/las-lluvias-en-el-norte-siguen%C2%A0provocando-cortes-en-ruta-9",
    },
    {
        "episode": "2022-01-17-perchel",
        "date": "2022-01-17",
        "place": "Volcán, Quebrada de los Filtros",
        "lat": -23.919,
        "lon": -65.463,
        "kind": "crecida",
        "summary": "Mismo día. El badén de los Filtros volvió a pasar agua y sedimento por la RN9.",
        "source": "Pregón",
        "url": "https://www.pregon.com.ar/nota/13556/2022/01/las-lluvias-en-el-norte-siguen%C2%A0provocando-cortes-en-ruta-9",
    },
    {
        "episode": "2022-12-07-uquia",
        "date": "2022-12-07",
        "place": "Uquía, El Bordo",
        "lat": -23.309,
        "lon": -65.356,
        "kind": "barro",
        "summary": "Corte en El Bordo. Lodo de quebradas y acequias. Micros y camiones varados entre Calete y Chucalezna.",
        "source": "El Tribuno de Jujuy",
        "url": "http://eltribunodejujuy.com/nota/2022-12-7-22-8-0-corte-de-ruta-e-inundacion-provoco-la-tormenta-anoche-en-uquia",
    },
    {
        "episode": "2023-01-25-huichaira",
        "date": "2023-01-25",
        "place": "Huichaira",
        "lat": -23.596,
        "lon": -65.401,
        "kind": "crecida",
        "summary": "Corte total en el arroyo Huichaira. Cerca de Uquía, media calzada por sedimento.",
        "source": "Jujuy a Diario",
        "url": "https://jujuyadiario.com/solicitan-transitar-con-precaucion-por-las-tormentas-en-la-quebrada-hay-cortes/",
    },
    {
        "episode": "2025-03-06-huacalera",
        "date": "2025-03-06",
        "place": "Huacalera, Quebrada Amarilla",
        "lat": -23.436,
        "lon": -65.351,
        "kind": "crecida",
        "summary": "Tormenta de Huacalera a Maimará, en carnaval. Filas de vehículos entre dos crecientes. Quebrada Amarilla quedó con extrema precaución.",
        "source": "El Tribuno de Jujuy",
        "url": "https://eltribunodejujuy.com/municipios/2025-3-6-22-7-0-tormenta-en-la-quebrada-cortes-en-la-rn-9-y-anegamientos-en-varias-localidades",
    },
    {
        "episode": "2025-03-06-huacalera",
        "date": "2025-03-06",
        "place": "Maimará",
        "lat": -23.624,
        "lon": -65.408,
        "kind": "crecida",
        "summary": "Mismo temporal. La lluvia llegó hasta Maimará y anegó calles además de la ruta.",
        "source": "El Tribuno de Jujuy",
        "url": "https://eltribunodejujuy.com/municipios/2025-3-6-22-7-0-tormenta-en-la-quebrada-cortes-en-la-rn-9-y-anegamientos-en-varias-localidades",
    },
)


def catalogo() -> dict:
    episodes = sorted({item["episode"] for item in CORTES})
    return {
        "route": "RN9",
        "corridor": "Bárcena a Humahuaca",
        "note": (
            "Cortes por lluvia, alud o barro publicados en prensa. "
            "No es el registro completo de Vialidad Nacional ni un parte de transitabilidad."
        ),
        "episode_count": len(episodes),
        "place_count": len(CORTES),
        "cortes": list(CORTES),
    }


def evaluar_corte(
    lat: float,
    lon: float,
    *,
    month: int | None,
    peak_index: float | None,
    confidence: float,
    name: str,
    period: str = "semana",
) -> dict:
    nearest = _nearest(lat, lon)
    if nearest["distance_km"] > CORRIDOR_KM:
        return {
            "place": {"name": name, "latitude": lat, "longitude": lon},
            "on_rn9": False,
            "distance_to_rn9_km": nearest["distance_km"],
            "nearest_cut": nearest["place"],
            "chance": None,
            "band": None,
            "operational": None,
            "headline": "Este punto queda lejos de la RN9 de la Quebrada. La chance de corte de esa ruta no se calcula acá.",
            "factors": [],
            "analogs": [],
            "limits": _limits(),
        }
    if month is None or peak_index is None:
        return _empty_week(name, lat, lon, nearest)
    rain_scale = max(0.0, min(peak_index, 100.0)) / 100.0
    history_weight = min(HISTORY_CAP, 8.0 * _episodes_near(lat, lon))
    season_weight = _season_weight(month)
    daily = period == "dia"
    rain_id, rain_label, rain_scope, when = (
        ("lluvia_dia", "Lluvia de ese día", "de ese día", "ese día")
        if daily
        else ("lluvia_semana", "Lluvia de esta semana", "de la semana", "esta semana")
    )
    factors = (
        {
            "id": rain_id,
            "label": rain_label,
            "points": round(RAIN_WEIGHT * rain_scale, 1),
            "detail": f"El índice {rain_scope} en el punto es {peak_index:.1f}. Aporta {RAIN_WEIGHT * rain_scale:.1f} pts.",
        },
        {
            "id": "historia_local",
            "label": "Cortes ya publicados cerca",
            "points": round(history_weight * rain_scale, 1),
            "detail": (
                f"{int(history_weight / 8)} episodio(s) a menos de {HISTORY_KM:.0f} km. "
                f"Esa historia solo pesa si {when} llueve."
            ),
        },
        {
            "id": "temporada",
            "label": "Mes en el catálogo",
            "points": round(season_weight * rain_scale, 1),
            "detail": f"El mes {month} concentra parte de los cortes publicados. Sin lluvia {rain_scope}, el mes no suma.",
        },
    )
    chance = round(min(100.0, sum(item["points"] for item in factors)), 1)
    physical = _band(chance)
    operational = "atencion" if confidence < 0.45 and physical == "baja" else physical
    analogs = _analogs(lat, lon)
    return {
        "place": {"name": name, "latitude": lat, "longitude": lon},
        "on_rn9": True,
        "distance_to_rn9_km": nearest["distance_km"],
        "nearest_cut": nearest["place"],
        "chance": chance,
        "band": physical,
        "operational": operational,
        "headline": _headline(name, operational, chance, analogs),
        "factors": list(factors),
        "analogs": analogs,
        "limits": _limits(),
    }


def lectura_de_semana(lat: float, lon: float, name: str, week: dict) -> dict:
    month = int(week["from"][5:7]) if week.get("from") else None
    peak_day = week.get("peak_day")
    confidence = 0.0
    for day in week.get("days") or []:
        if day.get("date") == peak_day:
            confidence = float(day.get("confidence") or 0)
            break
    reading = evaluar_corte(
        lat,
        lon,
        month=month,
        peak_index=week.get("peak_index"),
        confidence=confidence,
        name=name,
    )
    reading["week"] = {
        "from": week.get("from"),
        "to": week.get("to"),
        "peak_day": peak_day,
        "peak_index": week.get("peak_index"),
        "rain_sum_mm": week.get("rain_sum_mm"),
        "level": week.get("level"),
        "operational_level": week.get("operational_level"),
    }
    reading["days"] = dias_de_corte(lat, lon, name, week) if reading["on_rn9"] else []
    return reading


def dias_de_corte(lat: float, lon: float, name: str, week: dict) -> list[dict]:
    """La misma regla de la semana, día por día."""
    days = []
    for day in week.get("days") or []:
        date = day.get("date")
        index = day.get("index")
        if not date or index is None:
            days.append(
                {
                    "date": date,
                    "rain_mm": day.get("rain_mm"),
                    "index": None,
                    "chance": None,
                    "band": None,
                    "operational": "atencion",
                    "factors": [],
                    "note": "Día sin milímetros en la grilla. No se lee como ruta libre.",
                }
            )
            continue
        reading = evaluar_corte(
            lat,
            lon,
            month=int(date[5:7]),
            peak_index=index,
            confidence=float(day.get("confidence") or 0),
            name=name,
            period="dia",
        )
        days.append(
            {
                "date": date,
                "rain_mm": day.get("rain_mm"),
                "index": index,
                "chance": reading["chance"],
                "band": reading["band"],
                "operational": reading["operational"],
                "factors": reading["factors"],
                "note": None,
            }
        )
    return days


def pueblos() -> dict:
    return {
        "route": "RN9",
        "order": "Sur a norte, desde Volcán.",
        "pueblos": [
            {**pueblo, "episodes_near": _episodes_near(pueblo["lat"], pueblo["lon"])}
            for pueblo in PUEBLOS
        ],
    }


def tramo(desde: str, hasta: str) -> list[dict]:
    """Pueblos entre dos nombres, extremos incluidos, en orden de viaje."""
    names = [pueblo["name"] for pueblo in PUEBLOS]
    if desde not in names or hasta not in names:
        raise ValueError("Pueblo fuera de la traza de la RN9 de la Quebrada.")
    start, end = names.index(desde), names.index(hasta)
    step = 1 if end >= start else -1
    return [PUEBLOS[index] for index in range(start, end + step, step)]


def combinar_viaje(desde: str, hasta: str, lecturas: list[dict]) -> dict:
    """Un corte en cualquier pueblo corta el viaje: cada día manda el pueblo más comprometido."""
    dates = sorted({day["date"] for reading in lecturas for day in reading.get("days") or [] if day.get("date")})
    days = []
    for date in dates:
        towns = []
        for reading in lecturas:
            day = next((item for item in reading.get("days") or [] if item.get("date") == date), None)
            towns.append(
                {
                    "name": reading["place"]["name"],
                    "chance": day["chance"] if day else None,
                    "operational": day["operational"] if day else "atencion",
                    "rain_mm": day["rain_mm"] if day else None,
                }
            )
        known = [town for town in towns if town["chance"] is not None]
        complete = len(known) == len(towns)
        driver = max(known, key=lambda town: town["chance"]) if known else None
        operational = max((town["operational"] for town in towns), key=OPERATIONAL_RANK.__getitem__)
        if not complete and operational == "baja":
            operational = "atencion"
        rains = [town["rain_mm"] for town in towns if town["rain_mm"] is not None]
        days.append(
            {
                "date": date,
                "chance": driver["chance"] if driver else None,
                "operational": operational,
                "driver": driver["name"] if driver else None,
                "complete": complete,
                "max_rain_mm": max(rains) if rains else None,
                "towns": towns,
            }
        )
    eligible = [day for day in days if day["complete"]]
    best = min(eligible, key=lambda day: (day["chance"], day["date"])) if eligible else None
    worst = (
        max(days, key=lambda day: (OPERATIONAL_RANK[day["operational"]], day["chance"] or 0))
        if days
        else None
    )
    stops = [reading["place"]["name"] for reading in lecturas]
    return {
        "from": desde,
        "to": hasta,
        "stops": stops,
        "chance": worst["chance"] if worst else None,
        "operational": worst["operational"] if worst else "atencion",
        "worst_day": worst["date"] if worst else None,
        "best_day": best["date"] if best else None,
        "headline": _trip_headline(desde, hasta, worst, best),
        "days": days,
        "towns": lecturas,
        "cortes": _cortes_del_tramo(stops),
        "limits": [
            "La chance del viaje es la del pueblo más comprometido de cada día. No es una suma ni una probabilidad combinada.",
            *_limits(),
        ],
    }


def _trip_headline(desde: str, hasta: str, worst: dict | None, best: dict | None) -> str:
    trip = f"en {desde}" if desde == hasta else f"de {desde} a {hasta}"
    if worst is None:
        return f"Sin la lluvia de la semana no se dice que la RN9 {trip} esté libre."
    if worst["chance"] is None:
        opening = f"Para viajar {trip} falta la lluvia de algún día. No se declara la ruta libre."
    else:
        opening = (
            f"Para viajar {trip}, el día más comprometido es el {_fecha(worst['date'])}: "
            f"chance {worst['chance']:.1f} en {worst['driver']}."
        )
    if best is None:
        closing = " Ningún día tiene dato en todos los pueblos, así que no se marca un mejor día."
    else:
        closing = f" El día más tranquilo para salir es el {_fecha(best['date'])} (chance {best['chance']:.1f})."
    return opening + closing + " No es un parte de Vialidad ni una orden de cancelar el viaje."


_DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
_MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
          "septiembre", "octubre", "noviembre", "diciembre")


def _fecha(iso: str) -> str:
    try:
        day = datetime.date.fromisoformat(iso)
    except (TypeError, ValueError):
        return str(iso)
    return f"{_DIAS[day.weekday()]} {day.day} de {_MESES[day.month - 1]}"


def _cortes_del_tramo(stops: list[str]) -> list[dict]:
    points = [pueblo for pueblo in PUEBLOS if pueblo["name"] in stops]
    found = [
        item
        for item in CORTES
        if any(distance_m(p["lat"], p["lon"], item["lat"], item["lon"]) / 1000 <= HISTORY_KM for p in points)
    ]
    return sorted(found, key=lambda item: item["date"], reverse=True)


def _empty_week(name: str, lat: float, lon: float, nearest: dict) -> dict:
    return {
        "place": {"name": name, "latitude": lat, "longitude": lon},
        "on_rn9": True,
        "distance_to_rn9_km": nearest["distance_km"],
        "nearest_cut": nearest["place"],
        "chance": None,
        "band": None,
        "operational": "atencion",
        "headline": "Sin la lluvia de la semana no se dice que la RN9 va a seguir abierta.",
        "factors": [],
        "analogs": _analogs(lat, lon),
        "limits": _limits(),
    }


def _limits() -> list[str]:
    return [
        "No es un parte de Vialidad Nacional ni una orden de cancelar la excursión.",
        "La RN9 es la única traza continua de la Quebrada: un corte en otro pueblo deja este sin salida.",
        "El catálogo junta cortes publicados. Faltan los que no salieron en esas notas.",
        "No hay ráfaga de 30 minutos. Una tarde puede cerrar el badén aunque la semana se vea moderada.",
    ]


def _headline(name: str, operational: str, chance: float, analogs: list[dict]) -> str:
    where = analogs[0]["place"] if analogs else "esta traza"
    if operational == "atencion":
        return (
            f"Para salir de {name} por la RN9 esta semana la chance física es baja ({chance:.1f}). "
            "Igual no se declara la ruta tranquila: la grilla es gruesa y el pueblo no tiene otra salida."
        )
    return (
        f"Para una excursión en {name}, la chance de que la lluvia corte la RN9 es {operational} ({chance:.1f}). "
        f"El corte publicado más cercano es {where}. Un corte en la traza corta la logística de toda la Quebrada."
    )


def _band(chance: float) -> str:
    if chance < 25:
        return "baja"
    if chance < 50:
        return "media"
    if chance < 75:
        return "alta"
    return "muy_alta"


def _season_weight(month: int) -> float:
    counts: dict[int, set[str]] = {}
    for item in CORTES:
        counts.setdefault(int(item["date"][5:7]), set()).add(item["episode"])
    sizes = {key: len(value) for key, value in counts.items()}
    peak = max(sizes.values())
    return SEASON_CAP * sizes.get(month, 0) / peak


def _episodes_near(lat: float, lon: float) -> int:
    found = set()
    for item in CORTES:
        if distance_m(lat, lon, item["lat"], item["lon"]) / 1000 <= HISTORY_KM:
            found.add(item["episode"])
    return len(found)


def _nearest(lat: float, lon: float) -> dict:
    best = min(CORTES, key=lambda item: distance_m(lat, lon, item["lat"], item["lon"]))
    return {
        "place": best["place"],
        "distance_km": round(distance_m(lat, lon, best["lat"], best["lon"]) / 1000, 1),
    }


def _analogs(lat: float, lon: float) -> list[dict]:
    ranked = sorted(CORTES, key=lambda item: distance_m(lat, lon, item["lat"], item["lon"]))
    seen = set()
    analogs = []
    for item in ranked:
        if item["episode"] in seen:
            continue
        seen.add(item["episode"])
        analogs.append(
            {
                "episode": item["episode"],
                "date": item["date"],
                "place": item["place"],
                "kind": item["kind"],
                "distance_km": round(distance_m(lat, lon, item["lat"], item["lon"]) / 1000, 1),
                "summary": item["summary"],
                "source": item["source"],
                "url": item["url"],
            }
        )
        if len(analogs) == 4:
            break
    return analogs
