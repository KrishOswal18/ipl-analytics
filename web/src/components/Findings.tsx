import type { AllData } from "../types";
import { num, pct, pval } from "../lib";

export function Findings({ data }: { data: AllData }) {
  const s = data.summary;
  const ss = s.season_summary;
  const first = ss[0];
  const last = ss[ss.length - 1];
  const t = s.toss;
  const wp = s.winprob;
  const venues = [...data.venues.all].sort((a, b) => b.chase_win_pct - a.chase_win_pct);
  const bestChase = venues[0];
  const worstChase = venues[venues.length - 1];

  const items = [
    {
      n: "01",
      head: `First innings scores went from ${num(first.avg_first_innings)} to ${num(last.avg_first_innings)}`,
      body: `Averages sat between 150 and 172 for 15 seasons, then rose sharply from 2023, the first year of the Impact Player rule. Totals of 200 or more went from ${first.scores_200_plus} in ${first.season} to ${last.scores_200_plus} in ${last.season}, and sixes per match from ${first.sixes_per_match.toFixed(1)} to ${last.sixes_per_match.toFixed(1)}.`,
    },
    {
      n: "02",
      head: `Winning the toss alone is not significant: ${pct(t.overall.rate)} (${pval(t.overall.p_value)})`,
      body: `Toss winners won ${t.overall.wins} of ${t.overall.n} decided matches. The 95% interval (${pct(t.overall.ci_low)} to ${pct(t.overall.ci_high)}) includes 50%, and no era differs from the others (chi-square ${pval(t.era_chi2.p_value)}).`,
    },
    {
      n: "03",
      head: `Chasing is the real edge: ${pct(t.chasing.rate)} (${pval(t.chasing.p_value)})`,
      body: `Toss winners who fielded won ${pct(t.by_decision.field.rate)}, those who batted won ${pct(t.by_decision.bat.rate)} (chi-square ${pval(t.decision_chi2.p_value)}). Captains noticed: fielding first rose from ${pct(first.field_first_pct, 0)} of tosses in ${first.season} to ${pct(last.field_first_pct, 0)} in ${last.season}.`,
    },
    {
      n: "04",
      head: `Net run rate explains most of a season (r = ${s.nrr_fit.r.toFixed(2)})`,
      body: `Across ${s.nrr_fit.n} team-seasons, each +1.0 of NRR is worth about ${(s.nrr_fit.slope * 100).toFixed(0)} points of win %. Run rate differential is a better summary of a team than its win count in a 14 game season.`,
    },
    {
      n: "05",
      head: `Ground matters: chasing wins ${pct(bestChase.chase_win_pct, 0)} at ${bestChase.venue}, ${pct(worstChase.chase_win_pct, 0)} at ${worstChase.venue}`,
      body: `Among the ${data.venues.all.length} grounds with 20 or more decided matches. Samples are small, so treat single grounds with care: 30 matches gives an interval of roughly 18 points either way.`,
    },
    {
      n: "06",
      head: `Ball-by-ball win probability: ${pct(wp.model.accuracy)} accurate on seasons it never saw`,
      body: `Trained on ${wp.train_seasons[0]} to ${wp.train_seasons[1]}, tested on ${wp.test_seasons.join(" and ")} (${num(wp.n_test_states)} ball states, ${wp.n_test_matches} chases). Log-loss ${wp.model.log_loss.toFixed(3)} vs ${wp.baseline_constant.log_loss.toFixed(3)} for a constant guess. Adding the previous season's scoring rate fixed a clear calibration drift.`,
    },
  ];

  return (
    <div className="findings">
      {items.map((it) => (
        <article key={it.n} className="finding">
          <div className="finding-n">{it.n}</div>
          <h3>{it.head}</h3>
          <p>{it.body}</p>
        </article>
      ))}
    </div>
  );
}
