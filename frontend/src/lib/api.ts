// Typed API client — mirrors backend app/schemas (the contract). Uses native
// fetch with the signed-in user's Supabase access token attached as a bearer
// token, so the backend can scope every request to that user.
//
// In dev, VITE_API_BASE is empty → requests hit same-origin /api (Vite proxies
// to the backend). In prod it's the backend's URL (e.g. the Render service).

import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_BASE ?? "";

export type Band = { low: number; mid: number; high: number };

export type ColumnOverride = {
  timestamp?: number | null;
  value?: number | null;
  voltage?: number | null;
  headerRow?: number | null;
};

export type Tariff = {
  low: number;
  mid: number;
  high: number;
  currency: string;
  unit: string;
};

export type AnalysisConfig = {
  mode: "cv" | "energy";
  columnOverrides: Record<string, ColumnOverride>;
  occupiedStartHour: number;
  occupiedEndHour: number;
  workingDays: string[];
  tariff: Tariff;
  emissionFactorTco2PerMwh: number;
};

export type FileMeta = {
  filename: string;
  circuitName: string;
  loadType: string;
  rowCount: number;
  startTs: string | null;
  endTs: string | null;
  detectedCols: Record<string, number | null>;
  headerRow: number;
  warnings: string[];
};

export type UploadResponse = {
  analysisId: string;
  files: FileMeta[];
  warnings: string[];
};

export type AnalysisSummary = {
  id: string;
  name: string;
  createdAt: string;
  status: string;
};

export type CircuitResult = {
  filename: string;
  circuitName: string;
  loadType: string;
  kwh: Band;
  medianVoltage: number;
  voltageSubstituted: boolean;
  excludedFromTotals: boolean;
  rowCount: number;
};

export type LoadMixEntry = { loadType: string; kwh: number; share: number };

export type Results = {
  totalKwh: Band;
  averageLoadKw: number;
  baseloadKw: number;
  peakKw: number;
  intervalHours: number;
  periodDays: number;
  unoccupiedShare: number;
  unoccupiedWeekdayOffhoursShare: number;
  unoccupiedWeekendShare: number;
  hourlyProfile: { workingDays: number[]; offDays: number[] };
  loadMix: LoadMixEntry[];
  circuits: CircuitResult[];
  solar: CircuitResult[];
  periodCost: Band;
  annualCost: Band;
  periodCarbonTco2: number;
  annualCarbonTco2: number;
  recoverableCostLow: number;
  recoverableCostHigh: number;
  recoverableCarbonLow: number;
  recoverableCarbonHigh: number;
  assumptions: Record<string, unknown>;
  flags: Array<Record<string, unknown>>;
};

export type AnalysisDetail = {
  id: string;
  name: string;
  status: string;
  createdAt: string;
  config: AnalysisConfig | null;
  files: FileMeta[];
  results: Results | null;
};

export type EmissionFactor = {
  region: string;
  factor: number;
  unit: string;
  source: string;
  year: number;
};

export type TariffPreset = {
  id: string;
  region: string;
  low: number;
  mid: number;
  high: number;
  currency: string;
  unit: string;
  note: string;
};

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    if (res.status === 401)
      throw new Error("Your session expired — please log in again.");
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

// fetch wrapper that prefixes the API base and attaches the Supabase bearer
// token. For FormData bodies we leave Content-Type unset so the browser adds the
// multipart boundary itself.
async function authedFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  const headers = new Headers(init.headers);
  if (session) headers.set("Authorization", `Bearer ${session.access_token}`);
  return fetch(`${API_BASE}${path}`, { ...init, headers });
}

export const api = {
  upload: (files: File[]) => {
    const fd = new FormData();
    files.forEach((f) => fd.append("files", f));
    return authedFetch("/api/analyses", { method: "POST", body: fd }).then(
      json<UploadResponse>,
    );
  },
  list: () => authedFetch("/api/analyses").then(json<AnalysisSummary[]>),
  get: (id: string) =>
    authedFetch(`/api/analyses/${id}`).then(json<AnalysisDetail>),
  setConfig: (id: string, config: AnalysisConfig) =>
    authedFetch(`/api/analyses/${id}/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    }).then(json<{ ok: boolean }>),
  run: (id: string) =>
    authedFetch(`/api/analyses/${id}/run`, { method: "POST" }).then(
      json<{ results: Results }>,
    ),
  remove: (id: string) =>
    authedFetch(`/api/analyses/${id}`, { method: "DELETE" }).then(
      json<{ ok: boolean }>,
    ),
  emissionFactors: () =>
    authedFetch("/api/reference/emission-factors").then(json<EmissionFactor[]>),
  tariffs: () =>
    authedFetch("/api/reference/tariffs").then(json<TariffPreset[]>),
};

export const LOAD_TYPE_COLOR: Record<string, string> = {
  HVAC: "#5b8fc7",
  "General Power": "#f4b740",
  Lighting: "#e8c34b",
  UPS: "#57b894",
  Lift: "#9b8cc7",
  Ventilation: "#e8743b",
  Solar: "#8fae3b",
};

export const defaultConfig = (): AnalysisConfig => ({
  mode: "cv",
  columnOverrides: {},
  occupiedStartHour: 7,
  occupiedEndHour: 18,
  workingDays: ["Mon", "Tue", "Wed", "Thu", "Fri"],
  tariff: { low: 11, mid: 12, high: 13, currency: "INR", unit: "per kWh" },
  emissionFactorTco2PerMwh: 0.7117,
});
