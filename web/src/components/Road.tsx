import { TOWNS } from "@/lib/towns";

type Props = {
  townName: string;
  busy: boolean;
  onPick: (name: string) => void;
};

export function Road({ townName, busy, onPick }: Props) {
  const selected = Math.max(0, TOWNS.findIndex((town) => town.name === townName));
  return <section className="road" aria-label="Ruta 9 desde Volcán hacia Humahuaca">
    <p className="road-ask">{busy ? `Consultando ${townName}…` : "Estás en Volcán. Tocá hasta dónde llegás esta semana."}</p>
    <div className="road-line">
      {TOWNS.map((town, index) => <button
        key={town.name}
        type="button"
        aria-pressed={town.name === townName}
        disabled={busy}
        className={index <= selected ? "on-path" : undefined}
        onClick={() => onPick(town.name)}
      >
        <i />
        <span>{town.name}</span>
        {index === 0 && <small>Acá</small>}
      </button>)}
    </div>
  </section>;
}
