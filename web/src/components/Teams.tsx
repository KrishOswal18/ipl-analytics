import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AllData } from "../types";
import { C, Card, Stat, Tip, axisProps } from "./ui";
import { num, pct, short, signed } from "../lib";

export function Teams(props: {
  data: AllData;
  season: number | "all";
  team: string;
  onTeam: (short: string) => void;
}) {
  const { data, season } = props;
  const teams = data.teams.teams;
  const team = teams.find((t) => t.short === props.team) ?? teams[0];
  const srow = season === "all" ? null : team.seasons.find((s) => s.season === season) ?? null;

  const rows = team.seasons.map((s) => ({
    season: s.season,
    win: s.win_pct == null ? null : s.win_pct * 100,
    nrr: s.nrr,
    record: `${s.won}-${s.lost}${s.no_result ? `-${s.no_result}` : ""}`,
  }));

  const h2h = useMemo(
    () =>
      data.teams.head_to_head
        .filter((h) => h.team_1 === team.name || h.team_2 === team.name)
        .map((h) => {
          const me1 = h.team_1 === team.name;
          return {
            opp: me1 ? h.team_2 : h.team_1,
            won: me1 ? h.team_1_wins : h.team_2_wins,
            lost: me1 ? h.team_2_wins : h.team_1_wins,
            matches: h.matches,
          };
        })
        .sort((a, b) => b.matches - a.matches),
    [data, team],
  );

  return (
    <>
      <div className="team-picker" role="tablist" aria-label="team">
        {teams.map((t) => (
          <button
            key={t.short}
            role="tab"
            aria-selected={t.short === team.short}
            className={`team-chip ${t.short === team.short ? "active" : ""} ${t.active ? "" : "defunct"}`}
            onClick={() => props.onTeam(t.short)}
            title={t.name}
          >
            {t.short}
          </button>
        ))}
      </div>

      <div className="team-head">
        <div>
          <h3 className="team-name">{team.name}</h3>
          <p className="muted">
            {team.alltime.first_season} to {team.alltime.last_season}
            {!team.active && " (defunct)"}
            {team.titles.length > 0 && ` · Champions ${team.titles.join(", ")}`}
          </p>
        </div>
      </div>

      <div className="stat-row">
        {srow ? (
          <>
            <Stat label={`${season} record`} value={`${srow.won}-${srow.lost}`} note={srow.no_result ? `${srow.no_result} no result` : undefined} />
            <Stat label={`${season} win %`} value={pct(srow.win_pct)} accent />
            <Stat label={`${season} net run rate`} value={signed(srow.nrr, 3)} />
            <Stat label="scored per over" value={srow.run_rate_for?.toFixed(2) ?? "n/a"} />
            <Stat label="conceded per over" value={srow.run_rate_against?.toFixed(2) ?? "n/a"} />
          </>
        ) : (
          <>
            <Stat label="matches" value={team.alltime.played} />
            <Stat label="won" value={team.alltime.won} />
            <Stat label="lost" value={team.alltime.lost} />
            <Stat label="win % (decided)" value={pct(team.alltime.win_pct)} accent />
            <Stat label="titles" value={team.titles.length} />
          </>
        )}
        {season !== "all" && !srow && <p className="muted">{team.name} did not play in {season}.</p>}
      </div>

      <div className="grid-2">
        <Card title="Win % by season" sub="Decided matches only. Dashed line: 50%.">
          <div className="chart-h">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="season" {...axisProps} interval="preserveStartEnd" />
                <YAxis {...axisProps} domain={[0, 100]} />
                <ReferenceLine y={50} stroke={C.grey} strokeDasharray="4 4" />
                <Tooltip
                  cursor={{ fill: "rgba(94,224,255,0.06)" }}
                  content={<Tip fmt={(v) => `${v.toFixed(1)}%`} labelFmt={(l, p) => `${l} · ${String(p?.record ?? "")}`} />}
                />
                <Bar dataKey="win" name="win %" radius={[4, 4, 0, 0]}>
                  {rows.map((r) => (
                    <Cell key={r.season} fill={season === r.season ? C.orange : C.cyan} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
        <Card title="Net run rate by season" sub="Run rate scored minus conceded. Bowled out counts as 20 overs.">
          <div className="chart-h">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows} margin={{ top: 10, right: 8, left: -18, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="season" {...axisProps} interval="preserveStartEnd" />
                <YAxis {...axisProps} />
                <ReferenceLine y={0} stroke={C.grey} />
                <Tooltip cursor={{ fill: "rgba(94,224,255,0.06)" }} content={<Tip fmt={(v) => signed(v, 3)} />} />
                <Bar dataKey="nrr" name="NRR" radius={[4, 4, 0, 0]}>
                  {rows.map((r) => (
                    <Cell key={r.season} fill={(r.nrr ?? 0) >= 0 ? C.cyan : C.orange} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid-3">
        <Card title="Top run scorers for the franchise">
          <div className="tbl-wrap"><table className="tbl">
            <thead>
              <tr><th>Batter</th><th className="r">Runs</th><th className="r">SR</th></tr>
            </thead>
            <tbody>
              {team.top_batters.map((b) => (
                <tr key={b.batter}><td>{b.batter}</td><td className="r">{num(b.runs)}</td><td className="r">{b.strike_rate.toFixed(1)}</td></tr>
              ))}
            </tbody>
          </table></div>
        </Card>
        <Card title="Top wicket takers for the franchise">
          <div className="tbl-wrap"><table className="tbl">
            <thead>
              <tr><th>Bowler</th><th className="r">Wkts</th><th className="r">Econ</th></tr>
            </thead>
            <tbody>
              {team.top_bowlers.map((b) => (
                <tr key={b.bowler}><td>{b.bowler}</td><td className="r">{b.wickets}</td><td className="r">{b.economy.toFixed(2)}</td></tr>
              ))}
            </tbody>
          </table></div>
        </Card>
        <Card title="Head to head" sub="All seasons, decided matches">
          <div className="tbl-wrap"><table className="tbl">
            <thead>
              <tr><th>Opponent</th><th className="r">W-L</th><th className="r">Win %</th></tr>
            </thead>
            <tbody>
              {h2h.slice(0, 10).map((h) => (
                <tr key={h.opp}>
                  <td title={h.opp}>{short(h.opp)}</td>
                  <td className="r">{h.won}-{h.lost}</td>
                  <td className="r">{pct(h.won / h.matches, 0)}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
        </Card>
      </div>
    </>
  );
}
