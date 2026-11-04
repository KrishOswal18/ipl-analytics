"""Command line entry point.

    python -m ipl download   # fetch Cricsheet data into data/raw
    python -m ipl build      # clean + build tables into data/processed/ipl.duckdb
    python -m ipl analyse    # tests, model, charts, dashboard JSON
    python -m ipl run        # all of the above
"""

from __future__ import annotations

import json
import sys
import time

from . import DB_PATH, PROCESSED_DIR


def step_download():
    from .download import download
    download()


def step_build():
    from .ingest import load_deliveries, load_match_info
    from .tables import build_all, write_duckdb
    info = load_match_info()
    raw = load_deliveries()
    tables = build_all(info, raw)
    write_duckdb(tables)
    d = tables["deliveries"]
    print(f"Built {DB_PATH.name}: " + ", ".join(f"{k}={len(v):,}" for k, v in tables.items()))
    counts = {
        "matches": int(len(tables["matches"])),
        "decided": int(tables["matches"]["decided"].sum()),
        "no_result": int((~tables["matches"]["decided"]).sum()),
        "super_over_results": int(tables["matches"]["decided_by_super_over"].sum()),
        "dl_results": int(tables["matches"]["is_dl"].sum()),
        "deliveries": int(len(d)),
        "seasons": int(tables["matches"]["season"].nunique()),
        "first_season": int(tables["matches"]["season"].min()),
        "last_season": int(tables["matches"]["season"].max()),
        "players_batted": int(tables["batting_innings"]["batter"].nunique()),
        "raw_team_names": int(d["batting_team_raw"].nunique()),
        "clean_team_names": int(d["batting_team"].nunique()),
        "raw_venue_names": int(len(set(d["venue_raw"]) | set(tables["matches"]["venue_raw"]))),
        "clean_venue_names": int(tables["matches"]["venue"].nunique()),
        "raw_season_labels": sorted(set(d["season_label"])),
    }
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    (PROCESSED_DIR / "counts.json").write_text(json.dumps(counts, indent=2))
    print(json.dumps(counts))


def step_analyse():
    from . import analysis, charts, export, legacy, stats, winprob
    data = analysis.load_all()
    data["nrr_fit"] = analysis.nrr_vs_winpct(data["team_season"])
    toss = stats.toss_tests(data["matches"])
    venue_toss = stats.venue_toss_tests(data["matches"])
    o = toss["overall"]
    print(f"Toss: winner won {o['wins']}/{o['n']} = {o['rate']:.3f}, p = {o['p_value']:.3f}")

    deliveries = analysis.table(
        "deliveries", columns="match_id, innings, ball, actual_delivery, season, batting_team_raw, "
                              "total_runs, is_wicket, is_legal")
    season_rr = dict(zip(data["season_summary"]["season"].astype(int), data["season_summary"]["rr_overall"]))
    states = winprob.chase_states(deliveries, data["matches"], season_rr)
    wp = winprob.evaluate(states)
    print(f"Win prob: acc {wp['model']['accuracy']:.3f} log-loss {wp['model']['log_loss']:.3f} "
          f"(constant baseline acc {wp['baseline_constant']['accuracy']:.3f} "
          f"log-loss {wp['baseline_constant']['log_loss']:.3f})")
    cmp = legacy.compare(deliveries, data["matches"])
    print("v1 vs v2:", {k: round(v.get("accuracy_mean", v.get("accuracy", 0)), 3)
                        for k, v in cmp.items() if isinstance(v, dict) and "accuracy" in v})

    paths = charts.make_all(data, toss, wp, cmp)
    print(f"Saved {len(paths)} charts to reports/figures")
    counts = json.loads((PROCESSED_DIR / "counts.json").read_text())
    files = export.export(data, toss, wp, cmp, venue_toss, counts)
    print("Exported " + ", ".join(f"{p.name} ({p.stat().st_size/1024:.0f} KB)" for p in files))
    return data, toss, wp, cmp


def main(argv: list[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else "run"
    t0 = time.time()
    if cmd in ("download", "run"):
        step_download()
    if cmd in ("build", "run"):
        step_build()
    if cmd in ("analyse", "analyze", "run"):
        step_analyse()
    if cmd not in ("download", "build", "analyse", "analyze", "run"):
        print(__doc__)
        sys.exit(1)
    print(f"Done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main(sys.argv)
