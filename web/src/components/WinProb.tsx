import { useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import type { AllData } from "../types";
import { C, Card, Stat, Tip, axisProps } from "./ui";
import { chaseWinProbability, num, pct } from "../lib";

function Field(props: {
  label: string;
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (v: number) => void;
  suffix?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">
        {props.label}
        <strong>
          {props.step && props.step < 1 ? props.value.toFixed(2) : props.value}
          {props.suffix}
        </strong>
      </span>
      <input
        type="range"
        min={props.min}
        max={props.max}
        step={props.step ?? 1}
        value={props.value}
        onChange={(e) => props.onChange(Number(e.target.value))}
      />
    </label>
  );
}

export function WinProb({ data }: { data: AllData }) {
  const wp = data.summary.winprob;
  const ss = data.summary.season_summary;
  const latestRR = Number(ss[ss.length - 1].rr_overall.toFixed(2));
  const [target, setTarget] = useState(191);
  const [score, setScore] = useState(98);
  const [overs, setOvers] = useState(11);
  const [balls, setBalls] = useState(0);
  const [wkts, setWkts] = useState(3);
  const [prevRR, setPrevRR] = useState(latestRR);

  const legal = Math.min(overs * 6 + balls, 120);
  const ballsLeft = 120 - legal;
  const runsNeeded = target - score;
  const p = chaseWinProbability(wp, runsNeeded, ballsLeft, 10 - wkts, prevRR);
  const rrr = ballsLeft > 0 ? (runsNeeded * 6) / ballsLeft : 0;
  const crr = legal > 0 ? (score * 6) / legal : 0;

  const byWickets = useMemo(
    () =>
      Array.from({ length: 10 }, (_, w) => ({
        w: String(w),
        p: chaseWinProbability(wp, runsNeeded, ballsLeft, 10 - w, prevRR) * 100,
      })),
    [wp, runsNeeded, ballsLeft, prevRR],
  );

  const cal = wp.calibration.map((r, i) => ({
    x: Math.round(r.predicted * 100),
    model: r.observed * 100,
    without: wp.calibration_without_scoring_level[i]?.observed * 100,
  }));

  let status = `Needs ${runsNeeded} off ${ballsLeft} balls`;
  if (runsNeeded <= 0) status = "Target reached";
  else if (wkts >= 10) status = "All out";
  else if (ballsLeft <= 0) status = "Out of balls";

  const models = [
    { name: "Final model", s: wp.model, color: C.cyan },
    { name: "Same, no scoring level", s: wp.model_without_scoring_level, color: C.violet },
    { name: "Required run rate only", s: wp.baseline_required_rr, color: C.grey },
    { name: "Constant (train chase rate)", s: wp.baseline_constant, color: C.orange },
  ];

  return (
    <>
      <div className="grid-2">
        <Card title="Calculator" sub="Second innings of a 20 over game. Move the sliders.">
          <div className="fields">
            <Field label="Target" value={target} min={100} max={280} onChange={(v) => { setTarget(v); if (score >= v) setScore(v - 1); }} />
            <Field label="Current score" value={score} min={0} max={target} onChange={setScore} />
            <Field label="Overs completed" value={overs} min={0} max={19} onChange={setOvers} />
            <Field label="Extra balls this over" value={balls} min={0} max={5} onChange={setBalls} />
            <Field label="Wickets down" value={wkts} min={0} max={10} onChange={setWkts} />
            <Field label="Scoring level (last season's run rate)" value={prevRR} min={7} max={11} step={0.05} onChange={setPrevRR} />
          </div>
        </Card>
        <Card title="Chasing side win probability">
          <div className="gauge">
            <div className="gauge-value">{pct(p, 0)}</div>
            <div className="gauge-bar">
              <div className="gauge-fill" style={{ width: `${Math.round(p * 100)}%` }} />
            </div>
            <div className="gauge-labels">
              <span>bowling side {pct(1 - p, 0)}</span>
              <span>chasing side {pct(p, 0)}</span>
            </div>
          </div>
          <div className="stat-row tight">
            <Stat label="status" value={status} />
            <Stat label="required rate" value={ballsLeft > 0 && runsNeeded > 0 ? rrr.toFixed(2) : "n/a"} />
            <Stat label="current rate" value={legal > 0 ? crr.toFixed(2) : "n/a"} />
          </div>
          <p className="card-sub">Same position, different wickets down:</p>
          <div className="chart-s">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={byWickets} margin={{ top: 6, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} vertical={false} />
                <XAxis dataKey="w" {...axisProps} />
                <YAxis domain={[0, 100]} {...axisProps} />
                <Tooltip cursor={{ fill: "rgba(94,224,255,0.06)" }} content={<Tip fmt={(v) => `${v.toFixed(0)}%`} labelFmt={(l) => `${l} wickets down`} />} />
                <Bar dataKey="p" name="win %" radius={[4, 4, 0, 0]}>
                  {byWickets.map((r) => (
                    <Cell key={r.w} fill={Number(r.w) === wkts ? C.orange : C.cyan} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      <div className="grid-2">
        <Card
          title="How good is it?"
          sub={`Trained on ${wp.train_seasons[0]} to ${wp.train_seasons[1]} (${num(wp.n_train_states)} ball states). Tested on ${wp.test_seasons.join(" and ")}: ${num(wp.n_test_states)} states from ${wp.n_test_matches} chases it never saw.`}
        >
          <div className="tbl-wrap"><table className="tbl">
            <thead>
              <tr><th>Model</th><th className="r">Accuracy</th><th className="r">Log-loss</th><th className="r">Brier</th></tr>
            </thead>
            <tbody>
              {models.map((m) => (
                <tr key={m.name}>
                  <td><span className="dot" style={{ background: m.color }} />{m.name}</td>
                  <td className="r">{pct(m.s.accuracy)}</td>
                  <td className="r">{m.s.log_loss.toFixed(3)}</td>
                  <td className="r">{m.s.brier.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table></div>
          <p className="note">
            Lower log-loss and Brier are better. Accuracy at fixed points of the chase: after 6 overs{" "}
            {pct(wp.by_checkpoint["84"]?.accuracy, 0)}, after 11 overs {pct(wp.by_checkpoint["54"]?.accuracy, 0)}, after 16 overs{" "}
            {pct(wp.by_checkpoint["24"]?.accuracy, 0)}.
          </p>
        </Card>
        <Card title="Calibration on held-out seasons" sub="When the model says 40%, does the chaser win 40% of the time? Dashed line is perfect.">
          <div className="chart-h">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={cal} margin={{ top: 8, right: 12, left: -16, bottom: 0 }}>
                <CartesianGrid stroke={C.grid} />
                <XAxis dataKey="x" type="number" domain={[0, 100]} {...axisProps} unit="%" />
                <YAxis domain={[0, 100]} {...axisProps} />
                <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 100, y: 100 }]} stroke={C.grey} strokeDasharray="4 4" />
                <Tooltip content={<Tip fmt={(v) => `${v.toFixed(0)}%`} labelFmt={(l) => `predicted about ${l}%`} />} />
                <Legend wrapperStyle={{ color: C.muted, fontSize: 12 }} />
                <Line dataKey="model" name="final model" stroke={C.cyan} strokeWidth={2} dot={{ r: 3 }} />
                <Line dataKey="without" name="without scoring level" stroke={C.orange} strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </>
  );
}
