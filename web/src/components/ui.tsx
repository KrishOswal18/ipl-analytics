import type { ReactNode } from "react";

export const C = {
  bg: "#05090f",
  surface: "#0b121d",
  border: "#1a2433",
  grid: "#1a2433",
  text: "#eae5ec",
  muted: "#9aa3b2",
  cyan: "#5ee0ff",
  orange: "#f0904b",
  violet: "#b9a6ff",
  grey: "#5b6577",
};

export function Section(props: { id: string; kicker: string; title: string; lead?: ReactNode; children: ReactNode }) {
  return (
    <section id={props.id} className="section">
      <div className="kicker">{props.kicker}</div>
      <h2>{props.title}</h2>
      {props.lead && <p className="lead">{props.lead}</p>}
      {props.children}
    </section>
  );
}

export function Card(props: { title?: string; sub?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <div className={`card ${props.className ?? ""}`}>
      {props.title && <h3>{props.title}</h3>}
      {props.sub && <p className="card-sub">{props.sub}</p>}
      {props.children}
    </div>
  );
}

export function Stat(props: { label: string; value: ReactNode; note?: ReactNode; accent?: boolean }) {
  return (
    <div className="stat">
      <div className={`stat-value ${props.accent ? "accent" : ""}`}>{props.value}</div>
      <div className="stat-label">{props.label}</div>
      {props.note && <div className="stat-note">{props.note}</div>}
    </div>
  );
}

export function Pills<T extends string | number>(props: {
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
  label: string;
}) {
  return (
    <div className="pills" role="tablist" aria-label={props.label}>
      {props.options.map((o) => (
        <button
          key={String(o.value)}
          role="tab"
          aria-selected={o.value === props.value}
          className={o.value === props.value ? "pill active" : "pill"}
          onClick={() => props.onChange(o.value)}
        >
          {o.label}
        </button>
      ))}
    </div>
  );
}

interface TipPayload {
  name?: string;
  value?: number | string;
  color?: string;
  payload?: Record<string, unknown>;
}

export function Tip(props: {
  active?: boolean;
  payload?: TipPayload[];
  label?: string | number;
  fmt?: (v: number, name?: string) => string;
  labelFmt?: (l: string | number | undefined, p?: Record<string, unknown>) => string;
}) {
  if (!props.active || !props.payload?.length) return null;
  const head = props.labelFmt ? props.labelFmt(props.label, props.payload[0]?.payload) : props.label;
  return (
    <div className="tip">
      {head !== undefined && head !== "" && <div className="tip-head">{head}</div>}
      {props.payload.map((p, i) => (
        <div key={i} className="tip-row">
          <span className="tip-dot" style={{ background: p.color }} />
          <span className="tip-name">{p.name}</span>
          <span className="tip-val">
            {typeof p.value === "number" && props.fmt ? props.fmt(p.value, p.name) : String(p.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export const axisProps = {
  stroke: C.border,
  tick: { fill: C.muted, fontSize: 12 },
  tickLine: false,
} as const;
