import {
  CartesianGrid, ErrorBar, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from "recharts";
import type { AllData, Binom } from "../types";
import { C, Card, Stat, axisProps } from "./ui";
import { num, pct, pval } from "../lib";

function ciRows(entries: [string, Binom][]) {
  return entries.map(([label, b], i) => ({
    i,
    label,
    rate: b.rate * 100,
    err: [b.rate * 100 - b.ci_low * 100, b.ci_high * 100 - b.rate * 100],
    n: b.n,
    p: b.p_value,
  }));
}

function CiChart({ rows, color }: { rows: ReturnType<typeof ciRows>; color: string }) {
  return (
    <div className="chart-h">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 12, right: 12, left: -16, bottom: 4 }}>
          <CartesianGrid stroke={C.grid} vertical={false} />
          <XAxis
            type="number"
            dataKey="i"
            domain={[-0.5, rows.length - 0.5]}
            ticks={rows.map((r) => r.i)}
            tickFormatter={(i: number) => rows[i]?.label ?? ""}
            {...axisProps}
            tick={{ fill: C.muted, fontSize: 11 }}
          />
          <YAxis type="number" dataKey="rate" domain={[35, 70]} ticks={[35, 40, 45, 50, 55, 60, 65, 70]} {...axisProps} unit="%" />
          <ReferenceLine y={50} stroke={C.grey} strokeDasharray="4 4" />
          <Tooltip
            cursor={false}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null;
              const r = payload[0].payload as (typeof rows)[number];
              return (
                <div className="tip">
                  <div className="tip-head">{r.label}</div>
                  <div className="tip-row">win rate {r.rate.toFixed(1)}%</div>
                  <div className="tip-row">95% CI {(r.rate - r.err[0]).toFixed(1)} to {(r.rate + r.err[1]).toFixed(1)}</div>
                  <div className="tip-row">n = {r.n}, {pval(r.p)}</div>
                </div>
              );
            }}
          />
          <Scatter data={rows} fill={color} shape="circle">
            <ErrorBar dataKey="err" direction="y" stroke={color} strokeWidth={2} width={8} />
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}

export function Toss({ data }: { data: AllData }) {
  const t = data.summary.toss;
  const eras = Object.entries(t.by_era).map(([k, v]) => [k.replace(" (Impact Player)", " IP"), v] as [string, Binom]);
  const decision: [string, Binom][] = [["chose to bat", t.by_decision.bat], ["chose to field", t.by_decision.field]];
  const chaseEras = Object.entries(t.chasing_by_era).map(([k, v]) => [k.replace(" (Impact Player)", " IP"), v] as [string, Binom]);

  return (
    <>
      <div className="test-box">
        <div className="test-head">
          <span className="badge">Binomial test</span>
          <span className="muted">H0: P(toss winner wins) = 0.5, two-sided, alpha = 0.05</span>
        </div>
        <div className="stat-row">
          <Stat label="toss winner won" value={`${t.overall.wins} / ${num(t.overall.n)}`} />
          <Stat label="win rate" value={pct(t.overall.rate)} accent />
          <Stat label="95% interval" value={`${pct(t.overall.ci_low)} to ${pct(t.overall.ci_high)}`} />
          <Stat label="p-value" value={t.overall.p_value.toFixed(3)} note={t.overall.significant ? "significant" : "not significant"} />
        </div>
        <p>
          <strong>Result: no detectable toss effect.</strong> The interval includes 50%. With {num(t.overall.n)} matches the
          test could only reliably pick up an edge of about {t.mde_pp.toFixed(1)} points (80% power), so a small effect
          cannot be ruled out, but there is no evidence of one. Playoffs alone: {pct(t.by_stage.playoffs.rate)} of{" "}
          {t.by_stage.playoffs.n} ({pval(t.by_stage.playoffs.p_value)}).
        </p>
      </div>

      <div className="grid-3">
        <Card title="Toss winner win % by era" sub={`Chi-square across eras ${pval(t.era_chi2.p_value)}. IP = Impact Player era.`}>
          <CiChart rows={ciRows(eras)} color={C.cyan} />
        </Card>
        <Card
          title="By toss decision"
          sub={`Bat vs field differ: chi-square ${t.decision_chi2.chi2.toFixed(2)}, ${pval(t.decision_chi2.p_value)}.`}
        >
          <CiChart rows={ciRows(decision)} color={C.violet} />
        </Card>
        <Card title="Chasing side win % by era" sub={`Overall ${pct(t.chasing.rate)}, ${pval(t.chasing.p_value)}.`}>
          <CiChart rows={ciRows(chaseEras)} color={C.orange} />
        </Card>
      </div>
      <p className="note">
        Reading it together: the coin itself gives nothing, but fielding first does. Toss winners who fielded won{" "}
        {pct(t.by_decision.field.rate)}, those who batted {pct(t.by_decision.bat.rate)}. The chasing edge is strongest in 2013 to 2017
        and weakest since 2023 ({pct(t.chasing_by_era["2023-26 (Impact Player)"]?.rate)}), when bigger first innings totals made
        targets harder. Per ground tests: none of the {data.summary.venue_toss.length} grounds with 40+ matches is significant after a
        Bonferroni correction.
      </p>
    </>
  );
}
