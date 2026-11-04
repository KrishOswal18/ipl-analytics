import { useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { AllData } from "../types";
import { C, Card, Pills, Stat, Tip, axisProps } from "./ui";
import { num, pct, short } from "../lib";

type Metric = "score" | "phase" | "sixes" | "toss";

export function Seasons({ data, season }: { data: AllData; season: number | "all" }) {
  const ss = data.summary.season_summary;
  const [metric, setMetric] = useState<Metric>("score");
  const row = season === "all" ? null : ss.find((r) => r.season === season) ?? null;
  const champ = season === "all" ? null : data.summary.champions.find((c) => c.season === season);
  const rows = ss.map((r) => ({
    ...r,
    field_pct: r.field_first_pct * 100,
    chase_pct: r.chase_win_pct * 100,
  }));
  const hl = season === "all" ? undefined : season;

  return (
    <>
      <div className="stat-row">
        {row ? (
          <>
            <Stat label={`matches in ${row.season}`} value={row.matches} />
            <Stat label="avg first innings" value={num(row.avg_first_innings)} accent />
            <Stat label="200+ totals" value={row.scores_200_plus} />
            <Stat label="sixes per match" value={row.sixes_per_match.toFixed(1)} />
            <Stat label="chasing side won" value={pct(row.chase_win_pct, 0)} />
            <Stat label="champion" value={<span title={champ?.winner}>{short(champ?.winner) || "n/a"}</span>} note={champ?.winner} />
          </>
        ) : (
          <>
            <Stat label="seasons" value={data.summary.counts.seasons} />
            <Stat label="matches" value={num(data.summary.counts.matches)} accent />
            <Stat label="deliveries" value={num(data.summary.counts.deliveries)} />
            <Stat label="batters" value={num(data.summary.counts.players_batted)} />
            <Stat label="super-over results" value={data.summary.counts.super_over_results} />
            <Stat label="no results (excluded)" value={data.summary.counts.no_result} />
          </>
        )}
      </div>

      <Card>
        <Pills<Metric>
          label="season metric"
          value={metric}
          onChange={setMetric}
          options={[
            { value: "score", label: "First innings score" },
            { value: "phase", label: "Run rate by phase" },
            { value: "sixes", label: "Sixes per match" },
            { value: "toss", label: "Field first and chasing %" },
          ]}
        />
        <div className="chart-h">
          <ResponsiveContainer width="100%" height="100%">
            {metric === "sixes" ? (
              <BarChart data={rows} margin={{ top: 16, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="season" {...axisProps} interval="preserveStartEnd" />
                <YAxis {...axisProps} />
                <Tooltip cursor={{ fill: "rgba(94,224,255,0.06)" }} content={<Tip fmt={(v) => v.toFixed(1)} />} />
                <Bar dataKey="sixes_per_match" name="sixes per match" fill={C.cyan} radius={[4, 4, 0, 0]} />
                {hl && <ReferenceLine x={hl} stroke={C.orange} strokeDasharray="4 4" />}
              </BarChart>
            ) : (
              <LineChart data={rows} margin={{ top: 16, right: 12, left: -12, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="season" {...axisProps} interval="preserveStartEnd" />
                <YAxis {...axisProps} domain={metric === "toss" ? [0, 100] : ["auto", "auto"]} />
                <Tooltip
                  content={<Tip fmt={(v) => (metric === "toss" ? `${v.toFixed(1)}%` : v.toFixed(metric === "score" ? 0 : 2))} />}
                />
                {metric === "score" && (
                  <Line dataKey="avg_first_innings" name="avg first innings" stroke={C.cyan} strokeWidth={2} dot={{ r: 3 }} />
                )}
                {metric === "phase" && (
                  <>
                    <Line dataKey="rr_powerplay" name="powerplay (1-6)" stroke={C.cyan} strokeWidth={2} dot={{ r: 3 }} />
                    <Line dataKey="rr_middle" name="middle (7-15)" stroke={C.violet} strokeWidth={2} dot={{ r: 3 }} />
                    <Line dataKey="rr_death" name="death (16-20)" stroke={C.orange} strokeWidth={2} dot={{ r: 3 }} />
                    <Legend wrapperStyle={{ color: C.muted, fontSize: 12 }} />
                  </>
                )}
                {metric === "toss" && (
                  <>
                    <ReferenceLine y={50} stroke={C.grey} strokeDasharray="4 4" />
                    <Line dataKey="field_pct" name="toss winners fielding" stroke={C.cyan} strokeWidth={2} dot={{ r: 3 }} />
                    <Line dataKey="chase_pct" name="chasing side won" stroke={C.orange} strokeWidth={2} dot={{ r: 3 }} />
                    <Legend wrapperStyle={{ color: C.muted, fontSize: 12 }} />
                  </>
                )}
                {metric === "score" && <ReferenceLine x={2023} stroke={C.grey} strokeDasharray="4 4" label={{ value: "Impact Player", fill: C.muted, fontSize: 11, position: "insideTopLeft" }} />}
                {hl && <ReferenceLine x={hl} stroke={C.orange} strokeDasharray="4 4" />}
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
        <p className="note">
          {metric === "score" && "Average of first innings totals. Flat for 15 seasons, then about 20 runs higher from 2023."}
          {metric === "phase" && "Runs per over (legal balls) by phase. Powerplay scoring grew most."}
          {metric === "sixes" && "Sixes per match, super overs excluded."}
          {metric === "toss" && "Share of toss winners choosing to field, and how often the chasing side won."}
        </p>
      </Card>
    </>
  );
}
