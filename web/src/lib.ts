import type { AllData, WinProb } from "./types";

export async function loadData(): Promise<AllData> {
  const get = async <T,>(name: string): Promise<T> => {
    const res = await fetch(`/data/${name}.json`);
    if (!res.ok) throw new Error(`could not load ${name}.json (${res.status})`);
    return (await res.json()) as T;
  };
  const [summary, teams, venues, players] = await Promise.all([
    get<AllData["summary"]>("summary"),
    get<AllData["teams"]>("teams"),
    get<AllData["venues"]>("venues"),
    get<AllData["players"]>("players"),
  ]);
  return { summary, teams, venues, players };
}

export const pct = (v: number | null | undefined, digits = 1) =>
  v == null || Number.isNaN(v) ? "n/a" : `${(v * 100).toFixed(digits)}%`;

export const num = (v: number | null | undefined, digits = 0) =>
  v == null || Number.isNaN(v) ? "n/a" : v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });

export const pval = (p: number) => (p < 0.001 ? "p < 0.001" : `p = ${p.toFixed(p < 0.01 ? 4 : 3)}`);

export const signed = (v: number | null | undefined, digits = 2) =>
  v == null ? "n/a" : `${v > 0 ? "+" : ""}${v.toFixed(digits)}`;

export const SHORT: Record<string, string> = {
  "Chennai Super Kings": "CSK",
  "Delhi Capitals": "DC",
  "Deccan Chargers": "DCH",
  "Gujarat Lions": "GL",
  "Gujarat Titans": "GT",
  "Kochi Tuskers Kerala": "KTK",
  "Kolkata Knight Riders": "KKR",
  "Lucknow Super Giants": "LSG",
  "Mumbai Indians": "MI",
  "Pune Warriors": "PWI",
  "Punjab Kings": "PBKS",
  "Rajasthan Royals": "RR",
  "Rising Pune Supergiant": "RPS",
  "Royal Challengers Bengaluru": "RCB",
  "Sunrisers Hyderabad": "SRH",
};

export const short = (team: string | null | undefined) => (team ? SHORT[team] ?? team : "");

/**
 * Win probability for the chasing side. Mirrors ipl/winprob.py predict_raw:
 * logistic regression on raw features, coefficients exported by the pipeline.
 */
export function chaseWinProbability(
  wp: WinProb,
  runsNeeded: number,
  ballsLeft: number,
  wicketsLeft: number,
  prevRR: number,
): number {
  if (runsNeeded <= 0) return 1;
  if (wicketsLeft <= 0 || ballsLeft <= 0) return 0;
  const requiredRR = Math.min(Math.max((runsNeeded * 6) / Math.max(ballsLeft, 1), 0), 36);
  const x: Record<string, number> = {
    runs_needed: runsNeeded,
    balls_left: ballsLeft,
    wickets_left: wicketsLeft,
    required_rr: requiredRR,
    wkts_x_balls: (wicketsLeft * ballsLeft) / 120,
    rn_per_wkt: runsNeeded / Math.max(wicketsLeft, 1),
    prev_rr: prevRR,
  };
  let z = wp.coefficients.intercept;
  for (const [k, w] of Object.entries(wp.coefficients.weights)) z += w * (x[k] ?? 0);
  return 1 / (1 + Math.exp(-z));
}
