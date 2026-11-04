"""All report charts. Each function takes the data it needs and returns a figure.

`make_all` draws every chart and saves them to reports/figures as PNG.
The dark style matches the dashboard so the two read as one project.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402

from . import FIGURES_DIR  # noqa: E402
from .normalise import ACTIVE_TEAMS, ERA_ORDER, team_short  # noqa: E402

BG = "#05090f"
PANEL = "#0a111c"
TEXT = "#eae5ec"
MUTED = "#9aa3b2"
GRID = "#1c2635"
CYAN = "#5ee0ff"
ORANGE = "#f0904b"
VIOLET = "#b9a6ff"
GREY = "#5b6577"

SEQ = LinearSegmentedColormap.from_list("ipl_seq", ["#0d1a26", "#14506a", "#2a9cc0", CYAN, "#dff8ff"])


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
        "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "axes.titlecolor": TEXT,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.labelsize": 10, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "axes.spines.top": False, "axes.spines.right": False,
        "xtick.color": MUTED, "ytick.color": MUTED, "text.color": TEXT,
        "font.size": 10, "font.family": "DejaVu Sans", "legend.frameon": False,
        "lines.linewidth": 2, "figure.dpi": 110,
    })


def _fig(w=9, h=4.8):
    apply_style()
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_axisbelow(True)
    return fig, ax


def _note(fig, text):
    fig.text(0.01, 0.005, text, color=MUTED, fontsize=8, ha="left", va="bottom")


def _subtitle(ax, text):
    ax.text(0, 1.02, text, transform=ax.transAxes, color=MUTED, fontsize=9, va="bottom")


# 1
def matches_per_season(ss: pd.DataFrame):
    fig, ax = _fig()
    ax.bar(ss["season"], ss["matches"], color=CYAN, width=0.7)
    for s, n in zip(ss["season"], ss["matches"]):
        ax.text(s, n + 0.8, str(n), ha="center", color=MUTED, fontsize=8)
    ax.set_title("Matches per season in the dataset", pad=22)
    _subtitle(ax, f"{int(ss['matches'].sum())} matches, {int(ss['deliveries'].sum()):,} deliveries, 2008 to 2026")
    ax.set_xticks(ss["season"])
    ax.tick_params(axis="x", rotation=45)
    ax.set_ylabel("matches")
    ax.grid(axis="x", visible=False)
    return fig


# 2
def first_innings_trend(ss: pd.DataFrame):
    fig, ax = _fig()
    ax.plot(ss["season"], ss["avg_first_innings"], color=CYAN, marker="o", markersize=5)
    ax.axvline(2022.5, color=GREY, linestyle="--", linewidth=1)
    ax.text(2022.6, ss["avg_first_innings"].min(), "Impact Player\nrule from 2023", color=MUTED, fontsize=8)
    first, last = ss.iloc[0], ss.iloc[-1]
    ax.annotate(f"{first['avg_first_innings']:.0f}", (first["season"], first["avg_first_innings"]),
                textcoords="offset points", xytext=(0, 8), ha="center", color=TEXT)
    ax.annotate(f"{last['avg_first_innings']:.0f}", (last["season"], last["avg_first_innings"]),
                textcoords="offset points", xytext=(0, 8), ha="center", color=TEXT)
    ax.set_title("Average first innings score by season", pad=22)
    _subtitle(ax, "Scores were flat for 15 years, then jumped by about 20 runs after 2022")
    ax.set_ylabel("runs")
    ax.set_xticks(ss["season"])
    ax.tick_params(axis="x", rotation=45)
    return fig


# 3
def run_rate_by_phase(ss: pd.DataFrame):
    fig, ax = _fig()
    for col, label, color in (("rr_powerplay", "Powerplay (overs 1-6)", CYAN),
                              ("rr_middle", "Middle (7-15)", VIOLET),
                              ("rr_death", "Death (16-20)", ORANGE)):
        ax.plot(ss["season"], ss[col], color=color, marker="o", markersize=4, label=label)
        ax.text(ss["season"].iloc[-1] + 0.3, ss[col].iloc[-1], label.split(" ")[0], color=color,
                va="center", fontsize=9)
    ax.set_title("Run rate by phase of the innings", pad=22)
    _subtitle(ax, f"Powerplay {ss['rr_powerplay'].iloc[0]:.1f} to {ss['rr_powerplay'].iloc[-1]:.1f} an over, "
                  f"death overs {ss['rr_death'].iloc[0]:.1f} to {ss['rr_death'].iloc[-1]:.1f} (2008 vs 2026)")
    ax.set_ylabel("runs per over")
    ax.legend(loc="upper left")
    ax.set_xlim(ss["season"].min() - 0.5, ss["season"].max() + 2)
    ax.set_xticks(ss["season"])
    ax.tick_params(axis="x", rotation=45)
    return fig


# 4
def sixes_per_match(ss: pd.DataFrame):
    fig, ax = _fig()
    ax.bar(ss["season"], ss["sixes_per_match"], color=CYAN, width=0.7)
    ax.set_title("Sixes per match", pad=22)
    _subtitle(ax, f"{ss['sixes_per_match'].iloc[0]:.1f} in 2008, {ss['sixes_per_match'].iloc[-1]:.1f} in 2026")
    ax.set_xticks(ss["season"])
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="x", visible=False)
    return fig


# 5
def toss_decision_share(ss: pd.DataFrame):
    fig, ax = _fig()
    ax.plot(ss["season"], ss["field_first_pct"] * 100, color=CYAN, marker="o", markersize=5)
    ax.axhline(50, color=GREY, linestyle="--", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_title("Toss winners choosing to field first", pad=22)
    _subtitle(ax, "Captains moved from a coin flip in 2008 to fielding in about 4 of 5 tosses")
    ax.set_ylabel("% of tosses")
    ax.set_xticks(ss["season"])
    ax.tick_params(axis="x", rotation=45)
    return fig


def _ci_points(ax, labels, rows, color=CYAN):
    x = np.arange(len(labels))
    rates = np.array([r["rate"] for r in rows]) * 100
    lo = rates - np.array([r["ci_low"] for r in rows]) * 100
    hi = np.array([r["ci_high"] for r in rows]) * 100 - rates
    ax.errorbar(x, rates, yerr=[lo, hi], fmt="o", color=color, ecolor=color, elinewidth=2,
                capsize=5, markersize=9)
    for xi, r, row in zip(x, rates, rows):
        ax.text(xi + 0.08, r, f"{r:.1f}%\np={row['p_value']:.2f}\nn={row['n']}", color=TEXT,
                fontsize=8, va="center")
    ax.axhline(50, color=GREY, linestyle="--", linewidth=1)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_xlim(-0.5, len(labels) - 0.2)


# 6
def toss_by_era(toss: dict):
    fig, ax = _fig()
    rows = [toss["by_era"][e] for e in ERA_ORDER]
    _ci_points(ax, [e.replace(" (Impact Player)", "\n(Impact Player)") for e in ERA_ORDER], rows)
    o = toss["overall"]
    ax.set_title("Does the toss winner win the match? By era", pad=22)
    _subtitle(ax, f"Overall {o['rate']*100:.1f}% of {o['n']} decided matches, binomial p = {o['p_value']:.2f}. "
                  "Bars are 95% intervals, dashed line is a fair coin")
    ax.set_ylabel("toss winner win %")
    ax.set_ylim(35, 70)
    return fig


# 7
def toss_by_decision(toss: dict):
    fig, ax = _fig(7, 4.8)
    rows = [toss["by_decision"]["bat"], toss["by_decision"]["field"]]
    _ci_points(ax, ["chose to bat", "chose to field"], rows, color=CYAN)
    c = toss["decision_chi2"]
    ax.set_title("Toss winner win % by decision", pad=22)
    _subtitle(ax, f"Chi-square bat vs field: p = {c['p_value']:.3f}. The edge comes from chasing, not the coin")
    ax.set_ylabel("toss winner win %")
    ax.set_ylim(35, 65)
    return fig


# 8
def chasing_by_season(ss: pd.DataFrame, toss: dict):
    fig, ax = _fig()
    v = ss["chase_win_pct"] * 100 - 50
    colors = [CYAN if x >= 0 else ORANGE for x in v]
    ax.bar(ss["season"], v, bottom=50, color=colors, width=0.7)
    ax.axhline(50, color=GREY, linewidth=1)
    c = toss["chasing"]
    ax.set_title("Chasing side win % by season", pad=22)
    _subtitle(ax, f"Chasing won {c['rate']*100:.1f}% overall (p = {c['p_value']:.4f}). "
                  "Cyan: chasing ahead, orange: batting first ahead")
    ax.set_ylabel("chasing win %")
    ax.set_xticks(ss["season"])
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="x", visible=False)
    return fig


# 9
def team_alltime(ta: pd.DataFrame):
    df = ta[ta["played"] >= 40].sort_values("win_pct")
    fig, ax = _fig(9, 6)
    colors = [CYAN if t in ACTIVE_TEAMS else GREY for t in df["team"]]
    ax.barh(df["team"], df["win_pct"] * 100, color=colors, height=0.65)
    for y, (p, n) in enumerate(zip(df["win_pct"] * 100, df["played"])):
        ax.text(p + 0.5, y, f"{p:.1f}%  ({n})", va="center", color=TEXT, fontsize=8)
    ax.axvline(50, color=GREY, linestyle="--", linewidth=1)
    ax.set_title("All-time win % by franchise", pad=22)
    _subtitle(ax, "Old names merged into current ones. Grey: defunct franchises. Matches played in brackets")
    ax.set_xlim(0, 75)
    ax.set_xlabel("win % of decided matches")
    ax.grid(axis="y", visible=False)
    return fig


# 10
def team_season_heatmap(ts: pd.DataFrame):
    piv = ts.pivot(index="team", columns="season", values="win_pct")
    piv = piv.loc[piv.notna().sum(axis=1).sort_values(ascending=False).index]
    fig, ax = _fig(12, 6.5)
    ax.grid(False)
    im = ax.imshow(piv.to_numpy() * 100, cmap=SEQ, aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(piv.shape[1]))
    ax.set_xticklabels(piv.columns, rotation=45)
    ax.set_yticks(range(piv.shape[0]))
    ax.set_yticklabels([team_short(t) for t in piv.index])
    for i in range(piv.shape[0]):
        for j in range(piv.shape[1]):
            v = piv.iat[i, j]
            if pd.notna(v):
                ax.text(j, i, f"{v*100:.0f}", ha="center", va="center", fontsize=7,
                        color=BG if v > 0.55 else TEXT)
    cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.01)
    cb.ax.tick_params(colors=MUTED)
    cb.outline.set_edgecolor(GRID)
    ax.set_title("Win % by team and season", pad=22)
    _subtitle(ax, "Blank cells: the franchise did not play that season")
    return fig


# 11
def nrr_vs_winpct(ts: pd.DataFrame, fit: dict):
    fig, ax = _fig(8, 5.5)
    d = ts.dropna(subset=["nrr", "win_pct"])
    ax.scatter(d["nrr"], d["win_pct"] * 100, s=40, color=CYAN, alpha=0.75, edgecolor=BG, linewidth=1)
    xs = np.linspace(d["nrr"].min(), d["nrr"].max(), 50)
    ax.plot(xs, (fit["intercept"] + fit["slope"] * xs) * 100, color=ORANGE, linewidth=2)
    ax.set_title("Season net run rate vs season win %", pad=22)
    _subtitle(ax, f"{fit['n']} team-seasons, Pearson r = {fit['r']:.2f}. "
                  f"Each +1.0 NRR is worth about {fit['slope']*100:.0f} points of win %")
    ax.set_xlabel("net run rate (run rate differential)")
    ax.set_ylabel("win %")
    return fig


# 12
def venue_chase(vs: pd.DataFrame):
    df = vs.sort_values("chase_win_pct")
    fig, ax = _fig(9, 6.5)
    v = df["chase_win_pct"] * 100
    ax.barh(df["venue"], v - 50, left=50, color=[CYAN if x >= 50 else ORANGE for x in v], height=0.65)
    for y, (p, n) in enumerate(zip(v, df["matches"])):
        ax.text(max(p, 50) + 0.6, y, f"{p:.0f}%  (n={n})", va="center", color=TEXT, fontsize=8)
    ax.axvline(50, color=GREY, linewidth=1)
    ax.set_xlim(35, 75)
    ax.set_title("Chasing win % by ground", pad=22)
    _subtitle(ax, "Grounds with 20+ decided matches. Cyan: chasing team wins more")
    ax.set_xlabel("chasing side win %")
    ax.grid(axis="y", visible=False)
    return fig


# 13
def venue_par(vs: pd.DataFrame):
    df = vs.sort_values("avg_first_innings")
    fig, ax = _fig(9, 6.5)
    ax.barh(df["venue"], df["avg_first_innings"], color=VIOLET, height=0.65)
    for y, p in enumerate(df["avg_first_innings"]):
        ax.text(p + 1, y, f"{p:.0f}", va="center", color=TEXT, fontsize=8)
    ax.set_xlim(140, 190)
    ax.set_title("Average first innings score by ground", pad=22)
    _subtitle(ax, "All seasons pooled, so grounds used mostly in recent years look higher")
    ax.set_xlabel("runs")
    ax.grid(axis="y", visible=False)
    return fig


def _label_points(ax, df, x, y, name_col, n=8):
    for _, r in df.iterrows():
        ax.annotate(r[name_col], (r[x], r[y]), textcoords="offset points", xytext=(5, 4),
                    fontsize=8, color=TEXT)


# 14
def batter_sr_vs_avg(bc: pd.DataFrame):
    df = bc[bc["balls"] >= 1500].dropna(subset=["average"])
    fig, ax = _fig(9, 6)
    ax.scatter(df["average"], df["strike_rate"], s=np.clip(df["runs"] / 60, 10, 140), color=CYAN,
               alpha=0.6, edgecolor=BG, linewidth=1)
    top = pd.concat([df.nlargest(5, "strike_rate"), df.nlargest(5, "average"), df.nlargest(4, "runs")]).drop_duplicates("batter")
    _label_points(ax, top, "average", "strike_rate", "batter")
    ax.axhline(df["strike_rate"].median(), color=GREY, linestyle="--", linewidth=1)
    ax.axvline(df["average"].median(), color=GREY, linestyle="--", linewidth=1)
    ax.set_title("Batting average vs strike rate (career, 1500+ balls)", pad=22)
    _subtitle(ax, f"{len(df)} batters, dot size = career runs, dashed lines = medians")
    ax.set_xlabel("batting average")
    ax.set_ylabel("strike rate")
    return fig


# 15
def batter_consistency(bc: pd.DataFrame):
    df = bc[bc["innings"] >= 60].copy()
    df["pct25"] = df["pct_25_plus"] * 100
    fig, ax = _fig(9, 6)
    ax.scatter(df["pct25"], df["strike_rate"], s=36, color=VIOLET, alpha=0.7,
               edgecolor=BG, linewidth=1)
    top = pd.concat([df.nlargest(7, "pct_25_plus"), df.nlargest(3, "strike_rate")]).drop_duplicates("batter")
    _label_points(ax, top, "pct25", "strike_rate", "batter")
    ax.set_title("Consistency vs strike rate (60+ innings)", pad=22)
    _subtitle(ax, "Consistency = share of innings with 25 or more runs")
    ax.set_xlabel("% of innings with 25+ runs")
    ax.set_ylabel("strike rate")
    ax.scatter([df["pct_25_plus"].median() * 100], [df["strike_rate"].median()], marker="+", s=200, color=ORANGE)
    return fig


# 16
def top_order_sr_trend(bs: pd.DataFrame):
    top = bs.sort_values(["season", "runs"], ascending=[True, False]).groupby("season").head(20)
    agg = top.groupby("season").apply(lambda g: g["runs"].sum() * 100 / g["balls"].sum(), include_groups=False)
    fig, ax = _fig()
    ax.plot(agg.index, agg.values, color=CYAN, marker="o", markersize=5)
    ax.set_title("Strike rate of each season's top 20 run scorers", pad=22)
    _subtitle(ax, f"{agg.iloc[0]:.0f} in 2008 to {agg.iloc[-1]:.0f} in 2026, the leading batters now score much faster")
    ax.set_ylabel("combined strike rate")
    ax.set_xticks(agg.index)
    ax.tick_params(axis="x", rotation=45)
    return fig


# 17
def bowler_economy(bw: pd.DataFrame):
    df = bw[bw["balls"] >= 1200].nsmallest(15, "economy").sort_values("economy", ascending=False)
    fig, ax = _fig(9, 6)
    ax.barh(df["bowler"], df["economy"], color=CYAN, height=0.65)
    for y, (e, w) in enumerate(zip(df["economy"], df["wickets"])):
        ax.text(e + 0.05, y, f"{e:.2f}  ({int(w)} wkts)", va="center", color=TEXT, fontsize=8)
    ax.set_xlim(5.5, 8.6)
    ax.set_title("Most economical bowlers (career, 200+ overs)", pad=22)
    _subtitle(ax, "Runs conceded per over, wides and no-balls count against the bowler")
    ax.set_xlabel("economy rate")
    ax.grid(axis="y", visible=False)
    return fig


# 18
def dismissal_types(dm: pd.DataFrame):
    df = dm.sort_values("n")
    fig, ax = _fig(8, 5)
    ax.barh(df["wicket_type"], df["n"], color=VIOLET, height=0.65)
    tot = df["n"].sum()
    for y, n in enumerate(df["n"]):
        ax.text(n + 60, y, f"{n:,} ({n/tot*100:.1f}%)", va="center", color=TEXT, fontsize=8)
    ax.set_title("How batters got out", pad=22)
    _subtitle(ax, "All dismissals 2008 to 2026, super overs excluded")
    ax.set_xlim(0, df["n"].max() * 1.25)
    ax.grid(axis="y", visible=False)
    return fig


# 19
def winprob_calibration(wp: dict):
    fig, ax = _fig(7, 6)
    ax.plot([0, 100], [0, 100], color=GREY, linestyle="--", linewidth=1)
    for key, label, color in (("calibration_train", "training seasons (in sample)", GREY),
                              ("calibration_without_scoring_level", "2025-26, without scoring level", ORANGE),
                              ("calibration", "2025-26, final model", CYAN)):
        cal = pd.DataFrame(wp[key])
        ax.plot(cal["predicted"] * 100, cal["observed"] * 100, color=color, marker="o", markersize=7, label=label)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    m = wp["model"]
    ax.legend(loc="upper left")
    ax.set_title("Win probability calibration on held-out seasons", pad=22)
    _subtitle(ax, f"Final model: log-loss {m['log_loss']:.3f}, accuracy {m['accuracy']*100:.1f}%. "
                  "Closer to the dashed line is better")
    ax.set_xlabel("predicted chase win %")
    ax.set_ylabel("observed chase win %")
    return fig


# 20
def winprob_worm(test_frame: pd.DataFrame, matches: pd.DataFrame):
    final = matches[matches["is_final"] & matches["season"].isin(test_frame["season"].unique())]
    final = final[final["match_id"].isin(test_frame["match_id"])].sort_values("season").iloc[-1]
    w = test_frame[test_frame["match_id"] == final["match_id"]].copy()
    w["ball_no"] = 120 - w["balls_left"]
    fig, ax = _fig()
    ax.plot(w["ball_no"] / 6, w["p_model"] * 100, color=CYAN)
    ax.axhline(50, color=GREY, linestyle="--", linewidth=1)
    ax.set_ylim(0, 100)
    ax.set_title(f"{final['season']} final: {final['chasing_team']} chase win probability", pad=22)
    _subtitle(ax, f"Target {int(final['target'])}. Winner: {final['winner']}. Model never saw this season")
    ax.set_xlabel("overs into the chase")
    ax.set_ylabel("chasing side win %")
    return fig


# 21
def v1_vs_v2(cmp: dict):
    rows = [
        ("v1 as written\n(2008-22, random split)", cmp["v1_as_written_2008_2022"]["accuracy_mean"], GREY),
        ("v1 method\n(2008-26, random split)", cmp["v1_as_written_all_seasons"]["accuracy_mean"], GREY),
        ("real labels, no leakage\n(random split)", cmp["no_leakage_random_split"]["accuracy_mean"], VIOLET),
        ("same model,\nseason holdout", cmp["corrected_season_holdout"]["accuracy"], CYAN),
        ("logistic on score\n+ wickets, holdout", cmp["logistic_score_wickets_season_holdout"]["accuracy"], CYAN),
        ("always pick chaser\n(baseline)", cmp["baseline_majority_season_holdout"]["accuracy"], ORANGE),
    ]
    fig, ax = _fig(12, 5.2)
    x = np.arange(len(rows))
    ax.bar(x, [r[1] * 100 for r in rows], color=[r[2] for r in rows], width=0.6)
    for xi, r in zip(x, rows):
        ax.text(xi, r[1] * 100 + 0.7, f"{r[1]*100:.1f}%", ha="center", color=TEXT, fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([r[0] for r in rows], fontsize=8)
    ax.set_ylim(40, 75)
    ax.set_ylabel("accuracy, predicting the winner after innings 1")
    ax.set_title("My first predictor vs the corrected version", pad=22)
    _subtitle(ax, "Random split bars are the mean of 20 splits. Holdout = trained to 2024, tested on 2025 and 2026")
    ax.grid(axis="x", visible=False)
    return fig


def make_all(data: dict, toss: dict, wp: dict, cmp: dict, out_dir: Path = FIGURES_DIR) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.png"):
        old.unlink()
    ss = data["season_summary"]
    charts = [
        ("01_matches_per_season", lambda: matches_per_season(ss)),
        ("02_first_innings_trend", lambda: first_innings_trend(ss)),
        ("03_run_rate_by_phase", lambda: run_rate_by_phase(ss)),
        ("04_sixes_per_match", lambda: sixes_per_match(ss)),
        ("05_toss_decision_share", lambda: toss_decision_share(ss)),
        ("06_toss_winner_by_era", lambda: toss_by_era(toss)),
        ("07_toss_by_decision", lambda: toss_by_decision(toss)),
        ("08_chasing_by_season", lambda: chasing_by_season(ss, toss)),
        ("09_team_alltime_win_pct", lambda: team_alltime(data["team_alltime"])),
        ("10_team_season_heatmap", lambda: team_season_heatmap(data["team_season"])),
        ("11_nrr_vs_win_pct", lambda: nrr_vs_winpct(data["team_season"], data["nrr_fit"])),
        ("12_venue_chase_win_pct", lambda: venue_chase(data["venue_summary"])),
        ("13_venue_par_score", lambda: venue_par(data["venue_summary"])),
        ("14_batter_sr_vs_average", lambda: batter_sr_vs_avg(data["batter_career"])),
        ("15_batter_consistency", lambda: batter_consistency(data["batter_career"])),
        ("16_top_scorers_strike_rate", lambda: top_order_sr_trend(data["batter_season"])),
        ("17_bowler_economy", lambda: bowler_economy(data["bowler_career"])),
        ("18_dismissal_types", lambda: dismissal_types(data["dismissals"])),
        ("19_winprob_calibration", lambda: winprob_calibration(wp)),
        ("20_winprob_final_worm", lambda: winprob_worm(wp["_test_frame"], data["matches"])),
        ("21_v1_vs_v2_model", lambda: v1_vs_v2(cmp)),
    ]
    paths = []
    for name, fn in charts:
        fig = fn()
        p = out_dir / f"{name}.png"
        fig.savefig(p, bbox_inches="tight", dpi=130)
        plt.close(fig)
        paths.append(p)
    return paths
