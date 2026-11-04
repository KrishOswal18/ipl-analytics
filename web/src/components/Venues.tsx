import { useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AllData, VenueRow } from "../types";
import { C, Card, Tip, axisProps } from "./ui";
import { num, pct } from "../lib";

type SortKey = "matches" | "chase_win_pct" | "avg_first_innings" | "toss_winner_win_pct" | "field_first_pct";

export function Venues({ data, season }: { data: AllData; season: number | "all" }) {
  const [sort, setSort] = useState<SortKey>("matches");
  const minMatches = season === "all" ? 20 : 3;
  const list: VenueRow[] = useMemo(() => {
    const src = season === "all" ? data.venues.all : data.venues.by_season[String(season)] ?? [];
    return src.filter((v) => v.matches >= minMatches);
  }, [data, season, minMatches]);

  const sorted = [...list].sort((a, b) => (b[sort] ?? 0) - (a[sort] ?? 0));
  const chart = [...list]
    .sort((a, b) => b.chase_win_pct - a.chase_win_pct)
    .map((v) => ({ venue: v.venue, label: v.venue.length > 27 ? `${v.venue.slice(0, 25)}...` : v.venue, chase: v.chase_win_pct * 100, n: v.matches }));
  const h = Math.max(220, chart.length * 30 + 40);

  const head = (key: SortKey, label: string) => (
    <th className="r">
      <button className={`sort ${sort === key ? "on" : ""}`} onClick={() => setSort(key)}>
        {label}
      </button>
    </th>
  );

  return (
    <div className="venues">
      <Card
        title={`Chasing side win % ${season === "all" ? "(all seasons)" : `in ${season}`}`}
        sub={`Grounds with ${minMatches}+ decided matches${season === "all" ? "" : " that season"}. Cyan: chasing wins more often.`}
      >
        {chart.length === 0 ? (
          <p className="muted">No ground hosted {minMatches}+ matches this season.</p>
        ) : (
          <div style={{ height: h }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chart} layout="vertical" margin={{ top: 4, right: 16, left: 4, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} horizontal={false} />
                <XAxis type="number" domain={[0, 100]} {...axisProps} />
                <YAxis type="category" dataKey="label" width={190} {...axisProps} tick={{ fill: C.muted, fontSize: 11 }} />
                <ReferenceLine x={50} stroke={C.grey} strokeDasharray="4 4" />
                <Tooltip
                  cursor={{ fill: "rgba(94,224,255,0.06)" }}
                  content={<Tip fmt={(v) => `${v.toFixed(1)}%`} labelFmt={(_l, p) => `${String(p?.venue ?? "")} · ${String(p?.n ?? "")} matches`} />}
                />
                <Bar dataKey="chase" name="chasing win %" radius={[0, 4, 4, 0]} barSize={16}>
                  {chart.map((r) => (
                    <Cell key={r.venue} fill={r.chase >= 50 ? C.cyan : C.orange} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>
      <Card title="Ground table" sub="Tap a column to sort. Par = average first innings score.">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Ground</th>
                {head("matches", "Matches")}
                {head("chase_win_pct", "Chase win")}
                {head("avg_first_innings", "Par")}
                {head("toss_winner_win_pct", "Toss win")}
                {head("field_first_pct", "Field first")}
              </tr>
            </thead>
            <tbody>
              {sorted.map((v) => (
                <tr key={v.venue}>
                  <td>
                    {v.venue}
                    {v.city ? <span className="muted small"> · {v.city}</span> : null}
                  </td>
                  <td className="r">{v.matches}</td>
                  <td className="r">{pct(v.chase_win_pct, 0)}</td>
                  <td className="r">{num(v.avg_first_innings)}</td>
                  <td className="r">{pct(v.toss_winner_win_pct, 0)}</td>
                  <td className="r">{pct(v.field_first_pct, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
