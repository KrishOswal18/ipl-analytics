import { Bar, BarChart, CartesianGrid, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { AllData } from "../types";
import { C, Card, Tip, axisProps } from "./ui";
import { pct } from "../lib";

export function Versus({ data }: { data: AllData }) {
  const v = data.summary.v1_comparison;
  const rows = [
    { name: "v1 as written", note: "2008-22, random split", acc: v.v1_as_written_2008_2022.accuracy_mean!, sd: v.v1_as_written_2008_2022.accuracy_sd, color: C.grey },
    { name: "v1 method", note: "2008-26, random split", acc: v.v1_as_written_all_seasons.accuracy_mean!, sd: v.v1_as_written_all_seasons.accuracy_sd, color: C.grey },
    { name: "real labels, no leak", note: "random split", acc: v.no_leakage_random_split.accuracy_mean!, sd: v.no_leakage_random_split.accuracy_sd, color: C.violet },
    { name: "same RF, holdout", note: "train to 2024, test 2025-26", acc: v.corrected_season_holdout.accuracy, color: C.cyan },
    { name: "logistic, holdout", note: "score + wickets only", acc: v.logistic_score_wickets_season_holdout.accuracy, color: C.cyan },
    { name: "always chaser", note: "baseline", acc: v.baseline_majority_season_holdout.accuracy, color: C.orange },
  ].map((r) => ({ ...r, pct: r.acc * 100 }));

  return (
    <div className="grid-2">
      <Card
        title="Predicting the winner after the first innings"
        sub="My first project (ipl-match-predictor) reproduced on the same Cricsheet data, then fixed one problem at a time."
      >
        <div className="chart-h">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 44, left: 4, bottom: 0 }}>
              <CartesianGrid stroke={C.grid} horizontal={false} />
              <XAxis type="number" domain={[0, 80]} {...axisProps} unit="%" />
              <YAxis type="category" dataKey="name" width={124} {...axisProps} tick={{ fill: C.muted, fontSize: 11 }} />
              <Tooltip
                cursor={{ fill: "rgba(94,224,255,0.06)" }}
                content={<Tip fmt={(x) => `${x.toFixed(1)}%`} labelFmt={(l, p) => `${l} (${String(p?.note ?? "")})`} />}
              />
              <Bar dataKey="pct" name="accuracy" radius={[0, 4, 4, 0]} barSize={18}>
                <LabelList dataKey="pct" position="right" formatter={(v: number) => `${v.toFixed(1)}%`} fill={C.text} fontSize={12} />
                {rows.map((r) => (
                  <Cell key={r.name} fill={r.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="note">Random split bars are the mean of 20 different splits (v1 used one). Holdout test set: 144 matches, so about 8 points either way.</p>
      </Card>
      <Card title="What changed and what it was worth">
        <ul className="list">
          <li>
            <strong>Labels.</strong> v1 took the winner as "team 2 if it scored more, else team 1". Against Cricsheet's result fields that was
            wrong for {v.labels.wrong_winner} matches (all {v.labels.ties_or_super_overs} super-over ties went to the side batting first) and{" "}
            {v.labels.no_result_counted_as_result} no-results were counted as wins.
          </li>
          <li>
            <strong>Names.</strong> Delhi Daredevils and Delhi Capitals were two teams in v1, so were Kings XI Punjab and Punjab Kings. Now one franchise each.
          </li>
          <li>
            <strong>Leakage.</strong> Team win rates were computed on every match, test matches included. Now each match only sees results from
            before its date. This mattered less than expected ({pct(v.fixed_labels_still_leaky_random_split.accuracy_mean)} vs{" "}
            {pct(v.no_leakage_random_split.accuracy_mean)}), because a career win rate barely moves.
          </li>
          <li>
            <strong>Evaluation.</strong> A season holdout is how the model would really be used. The same random forest gets{" "}
            {pct(v.corrected_season_holdout.accuracy)} on 2025 and 2026, and a two-feature logistic regression does as well (
            {pct(v.logistic_score_wickets_season_holdout.accuracy)}). Always picking the chasing side: {pct(v.baseline_majority_season_holdout.accuracy)}.
          </li>
        </ul>
      </Card>
    </div>
  );
}
