import { useState } from "react";
import type { AllData } from "../types";
import { Card, Pills } from "./ui";
import { num, pct, short } from "../lib";

type Board = "runs" | "sr" | "consistency" | "bowling";

export function Players({ data, season }: { data: AllData; season: number | "all" }) {
  const [board, setBoard] = useState<Board>("sr");
  const [showAll, setShowAll] = useState(false);
  const limit = showAll ? 30 : 15;
  const key = season === "all" ? "all" : String(season);
  const th = data.players.thresholds;
  const p = data.players;
  const isAll = season === "all";

  const subs: Record<Board, string> = {
    runs: isAll ? `Career, ${th.career_min_balls}+ balls faced. SR rank is among all qualified batters.` : `${season} season, ${th.season_min_balls}+ balls faced.`,
    sr: isAll
      ? `Strike rate = runs per 100 balls. Career, ${th.career_min_balls}+ balls. Ranked with a SQL window function.`
      : `RANK() OVER (PARTITION BY season ORDER BY strike rate) among batters with ${th.season_min_balls}+ balls in ${season}.`,
    consistency: isAll
      ? `Share of innings with 25+ runs, ${th.consistency_min_innings}+ innings. CV = std / mean of scores, lower is steadier.`
      : `Share of innings with 25+ runs in ${season}, ${th.season_consistency_min_innings}+ innings.`,
    bowling: isAll
      ? `Career wickets, ${th.bowl_career_min_balls}+ balls bowled. Run outs do not count to the bowler.`
      : `${season} wickets, ${th.bowl_season_min_balls}+ balls bowled.`,
  };

  return (
    <Card>
      <Pills<Board>
        label="leaderboard"
        value={board}
        onChange={setBoard}
        options={[
          { value: "sr", label: "Strike rate" },
          { value: "consistency", label: "Consistency" },
          { value: "runs", label: "Runs" },
          { value: "bowling", label: "Bowling" },
        ]}
      />
      <p className="card-sub">{subs[board]}</p>
      <div className="tbl-wrap">
        {(board === "runs" || board === "sr") && (
          <table className="tbl">
            <thead>
              <tr>
                <th className="r">#</th><th>Batter</th><th>Team</th><th className="r">Inns</th><th className="r">Runs</th>
                <th className="r">Balls</th><th className="r">SR</th><th className="r">Avg</th><th className="r">6s</th>
                <th className="r">SR rank</th>
              </tr>
            </thead>
            <tbody>
              {(board === "runs" ? p.batting[key] : p.strike_rate[key])?.slice(0, limit).map((r, i) => (
                <tr key={r.batter}>
                  <td className="r muted">{i + 1}</td>
                  <td>{r.batter}</td>
                  <td title={r.team ?? ""}>{short(r.team)}</td>
                  <td className="r">{r.innings}</td>
                  <td className="r">{num(r.runs)}</td>
                  <td className="r">{num(r.balls)}</td>
                  <td className={`r ${board === "sr" ? "hl" : ""}`}>{r.strike_rate.toFixed(1)}</td>
                  <td className="r">{r.average == null ? "n/a" : r.average.toFixed(1)}</td>
                  <td className="r">{r.sixes}</td>
                  <td className="r muted">{r.sr_rank}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {board === "consistency" && (
          <table className="tbl">
            <thead>
              <tr>
                <th className="r">#</th><th>Batter</th><th>Team</th><th className="r">Inns</th><th className="r">Runs</th>
                <th className="r">25+ share</th><th className="r">Median</th><th className="r">CV</th><th className="r">SR</th>
              </tr>
            </thead>
            <tbody>
              {p.consistency[key]?.slice(0, limit).map((r, i) => (
                <tr key={r.batter}>
                  <td className="r muted">{i + 1}</td>
                  <td>{r.batter}</td>
                  <td title={r.team ?? ""}>{short(r.team)}</td>
                  <td className="r">{r.innings}</td>
                  <td className="r">{num(r.runs)}</td>
                  <td className="r hl">{pct(r.pct_25_plus, 0)}</td>
                  <td className="r">{r.median_score}</td>
                  <td className="r">{r.cv == null ? "n/a" : r.cv.toFixed(2)}</td>
                  <td className="r">{r.strike_rate == null ? "n/a" : r.strike_rate.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {board === "bowling" && (
          <table className="tbl">
            <thead>
              <tr>
                <th className="r">#</th><th>Bowler</th><th>Team</th><th className="r">Balls</th><th className="r">Wkts</th>
                <th className="r">Econ</th><th className="r">Dot %</th><th className="r">Balls/wkt</th>
              </tr>
            </thead>
            <tbody>
              {p.bowling[key]?.slice(0, limit).map((r, i) => (
                <tr key={r.bowler}>
                  <td className="r muted">{i + 1}</td>
                  <td>{r.bowler}</td>
                  <td title={r.team ?? ""}>{short(r.team)}</td>
                  <td className="r">{num(r.balls)}</td>
                  <td className="r hl">{r.wickets}</td>
                  <td className="r">{r.economy.toFixed(2)}</td>
                  <td className="r">{pct(r.dot_pct, 0)}</td>
                  <td className="r">{r.balls_per_wicket == null ? "n/a" : r.balls_per_wicket.toFixed(1)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      <button className="pill more" onClick={() => setShowAll((v) => !v)}>
        {showAll ? "Show top 15" : "Show top 30"}
      </button>
    </Card>
  );
}
