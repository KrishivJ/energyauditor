import { useEffect, useState } from "react";
import type { AnalysisConfig, EmissionFactor, TariffPreset } from "../lib/api";
import { api } from "../lib/api";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function ConfigPanel({
  config,
  onChange,
}: {
  config: AnalysisConfig;
  onChange: (c: AnalysisConfig) => void;
}) {
  const [tariffs, setTariffs] = useState<TariffPreset[]>([]);
  const [factors, setFactors] = useState<EmissionFactor[]>([]);

  useEffect(() => {
    api
      .tariffs()
      .then(setTariffs)
      .catch(() => {});
    api
      .emissionFactors()
      .then(setFactors)
      .catch(() => {});
  }, []);

  const set = (patch: Partial<AnalysisConfig>) =>
    onChange({ ...config, ...patch });
  const toggleDay = (d: string) =>
    set({
      workingDays: config.workingDays.includes(d)
        ? config.workingDays.filter((x) => x !== d)
        : [...config.workingDays, d],
    });

  return (
    <div className="panel space-y-5 p-6">
      <h2 className="font-display text-lg font-semibold">Assumptions</h2>
      <p className="-mt-2 text-sm text-muted">
        Every figure depends on these. Change them and re-run; nothing material
        is hidden.
      </p>

      <div>
        <div className="label mb-1">Meter mode</div>
        <div className="flex gap-2">
          {(["cv", "energy"] as const).map((m) => (
            <button
              key={m}
              className={`btn ${config.mode === m ? "btn-primary" : ""}`}
              onClick={() => set({ mode: m })}
            >
              {m === "cv" ? "Current + Voltage" : "Energy (kWh) direct"}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <label className="block">
          <div className="label mb-1">Occupied from (h)</div>
          <input
            type="number"
            min={0}
            max={23}
            className="input w-full"
            value={config.occupiedStartHour}
            onChange={(e) => set({ occupiedStartHour: Number(e.target.value) })}
          />
        </label>
        <label className="block">
          <div className="label mb-1">Occupied to (h)</div>
          <input
            type="number"
            min={0}
            max={24}
            className="input w-full"
            value={config.occupiedEndHour}
            onChange={(e) => set({ occupiedEndHour: Number(e.target.value) })}
          />
        </label>
      </div>

      <div>
        <div className="label mb-1">Working days</div>
        <div className="flex flex-wrap gap-1.5">
          {DAYS.map((d) => (
            <button
              key={d}
              className={`btn px-3 py-1 ${
                config.workingDays.includes(d) ? "btn-primary" : ""
              }`}
              onClick={() => toggleDay(d)}
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      <div>
        <div className="label mb-1">
          Tariff band ({config.tariff.currency} / kWh)
        </div>
        {tariffs.length > 0 && (
          <select
            className="input mb-2 w-full"
            onChange={(e) => {
              const t = tariffs.find((x) => x.id === e.target.value);
              if (t)
                set({
                  tariff: {
                    low: t.low,
                    mid: t.mid,
                    high: t.high,
                    currency: t.currency,
                    unit: t.unit,
                  },
                });
            }}
            defaultValue=""
          >
            <option value="" disabled>
              Load a preset…
            </option>
            {tariffs.map((t) => (
              <option key={t.id} value={t.id}>
                {t.region} ({t.low}/{t.mid}/{t.high})
              </option>
            ))}
          </select>
        )}
        <div className="grid grid-cols-3 gap-2">
          {(["low", "mid", "high"] as const).map((k) => (
            <label key={k} className="block">
              <div className="text-xs text-muted">{k}</div>
              <input
                type="number"
                step="0.1"
                className="input w-full"
                value={config.tariff[k]}
                onChange={(e) =>
                  set({
                    tariff: { ...config.tariff, [k]: Number(e.target.value) },
                  })
                }
              />
            </label>
          ))}
        </div>
        <p className="mt-1.5 text-xs text-amber/80">
          Tariff is the softest input — confirm against an actual bill.
        </p>
      </div>

      <label className="block">
        <div className="label mb-1">Emission factor (tCO₂ / MWh)</div>
        <input
          type="number"
          step="0.0001"
          className="input w-full"
          value={config.emissionFactorTco2PerMwh}
          onChange={(e) =>
            set({ emissionFactorTco2PerMwh: Number(e.target.value) })
          }
        />
        {factors[0] && (
          <p className="mt-1 text-xs text-muted">{factors[0].source}</p>
        )}
      </label>
    </div>
  );
}
