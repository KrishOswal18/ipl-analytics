import { useEffect, useState } from "react";
import type { AllData } from "./types";
import { loadData, num } from "./lib";
import { Section } from "./components/ui";
import { Findings } from "./components/Findings";
import { Seasons } from "./components/Seasons";
import { Teams } from "./components/Teams";
import { Venues } from "./components/Venues";
import { Toss } from "./components/Toss";
import { Players } from "./components/Players";
import { WinProb } from "./components/WinProb";
import { Versus } from "./components/Versus";

const REPO = "https://github.com/KrishOswal18/ipl-analytics";

function readHash() {
  const h = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const s = h.get("season");
  return { season: s && /^\d{4}$/.test(s) ? Number(s) : ("all" as const), team: h.get("team") ?? "CSK" };
}

export default function App() {
  const [data, setData] = useState<AllData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const init = readHash();
  const [season, setSeason] = useState<number | "all">(init.season);
  const [team, setTeam] = useState<string>(init.team);

  useEffect(() => {
    loadData().then(setData).catch((e: Error) => setError(e.message));
  }, []);

  useEffect(() => {
    const h = new URLSearchParams();
    if (season !== "all") h.set("season", String(season));
    if (team !== "CSK") h.set("team", team);
    const str = h.toString();
    window.history.replaceState(null, "", str ? `#${str}` : window.location.pathname);
  }, [season, team]);

  if (error) return <div className="loading">Could not load data: {error}</div>;
  if (!data) return <div className="loading">Loading 19 seasons of IPL data...</div>;

  const c = data.summary.counts;
  const nav = [
    ["findings", "Findings"],
    ["seasons", "Seasons"],
    ["teams", "Teams"],
    ["venues", "Venues"],
    ["toss", "Toss"],
    ["players", "Players"],
    ["winprob", "Win probability"],
    ["method", "Method"],
  ];

  return (
    <>
      <header className="top">
        <div className="top-inner">
          <a className="brand" href="#">
            IPL<span>analytics</span>
          </a>
          <nav className="nav">
            {nav.map(([id, label]) => (
              <a key={id} href={`#${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(id)?.scrollIntoView({ behavior: "smooth" }); }}>
                {label}
              </a>
            ))}
          </nav>
          <label className="season-select">
            <span>Season</span>
            <select value={String(season)} onChange={(e) => setSeason(e.target.value === "all" ? "all" : Number(e.target.value))}>
              <option value="all">All seasons</option>
              {[...data.summary.seasons].reverse().map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="kicker">Krish Oswal · data project</div>
          <h1>
            19 seasons of IPL, <span className="accent">ball by ball</span>
          </h1>
          <p className="lead">
            {num(c.deliveries)} deliveries from {num(c.matches)} matches ({c.first_season} to {c.last_season}), cleaned from raw Cricsheet
            files. Does the toss matter? Which grounds favour chasing? Who scores fastest and most reliably? Each answer below comes
            with the number behind it.
          </p>
          <div className="hero-links">
            <a className="btn" href="#findings" onClick={(e) => { e.preventDefault(); document.getElementById("findings")?.scrollIntoView({ behavior: "smooth" }); }}>
              Key findings
            </a>
            <a className="btn ghost" href={REPO} target="_blank" rel="noreferrer">
              Code on GitHub
            </a>
          </div>
        </section>

        <Section id="findings" kicker="01 · Story" title="Key findings">
          <Findings data={data} />
        </Section>

        <Section
          id="seasons"
          kicker="02 · Seasons"
          title="How the game changed"
          lead="Pick a season in the top bar to see its numbers. The charts mark the selected season."
        >
          <Seasons data={data} season={season} />
        </Section>

        <Section
          id="teams"
          kicker="03 · Teams"
          title="Franchise pages"
          lead="Old names are merged into the current franchise (Delhi Daredevils into Delhi Capitals, Kings XI Punjab into Punjab Kings). Deccan Chargers and Sunrisers Hyderabad stay separate."
        >
          <Teams data={data} season={season} team={team} onTeam={setTeam} />
        </Section>

        <Section id="venues" kicker="04 · Venues" title="Where chasing pays" lead={`${c.raw_venue_names} raw venue spellings were cleaned down to ${c.clean_venue_names} grounds.`}>
          <Venues data={data} season={season} />
        </Section>

        <Section id="toss" kicker="05 · Toss" title="Does winning the toss win the match?">
          <Toss data={data} />
        </Section>

        <Section id="players" kicker="06 · Players" title="Strike rate and consistency leaderboards">
          <Players data={data} season={season} />
        </Section>

        <Section
          id="winprob"
          kicker="07 · Model"
          title="Chase win probability"
          lead="A logistic regression on the state of the chase: runs needed, balls left, wickets left and the scoring level of the era. It runs in your browser from coefficients exported by the Python pipeline."
        >
          <WinProb data={data} />
          <h3 className="sub-h">Compared with my first predictor</h3>
          <Versus data={data} />
        </Section>

        <Section id="method" kicker="08 · Method" title="How this was built">
          <div className="grid-3">
            <div className="card">
              <h3>Pipeline</h3>
              <p className="card-sub">
                Python package: download, normalise (team, venue and season alias maps), build match, innings, team-match, batting and
                bowling tables in DuckDB, then SQL files with window functions for rankings. 63 pytest tests cover the cleaning and
                feature functions.
              </p>
            </div>
            <div className="card">
              <h3>Statistics</h3>
              <p className="card-sub">
                Exact binomial tests with Wilson intervals, chi-square tests for decision and era, Bonferroni for per-ground tests. The
                model is evaluated on whole held-out seasons, never a random split of balls.
              </p>
            </div>
            <div className="card">
              <h3>Cleaning in numbers</h3>
              <p className="card-sub">
                {c.raw_team_names} raw team names to {c.clean_team_names} franchises, {c.raw_venue_names} venue strings to{" "}
                {c.clean_venue_names} grounds, season labels like "2007/08" mapped to calendar years, {c.super_over_results} super-over
                results credited to the super-over winner, {c.no_result} no-results excluded.
              </p>
            </div>
          </div>
        </Section>
      </main>

      <footer className="foot">
        <p>
          Built by Krish Oswal, B.Tech CSE, Vishwakarma University, Pune. <a href={REPO}>Source code</a>.
        </p>
        <p className="muted small">
          Data: ball-by-ball IPL data from <a href="https://cricsheet.org">Cricsheet</a>, available under the Open Data Commons
          Attribution License (ODC-By 1.0). Covers {c.first_season} to {c.last_season}.
        </p>
      </footer>
    </>
  );
}
