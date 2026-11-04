export interface Binom {
  wins: number;
  n: number;
  rate: number;
  ci_low: number;
  ci_high: number;
  p_value: number;
  significant: boolean;
  field_first_pct?: number;
}

export interface Chi2 {
  chi2: number;
  dof: number;
  p_value: number;
  significant: boolean;
}

export interface SeasonRow {
  season: number;
  matches: number;
  decided: number;
  avg_first_innings: number;
  field_first_pct: number;
  toss_winner_win_pct: number;
  chase_win_pct: number;
  scores_200_plus: number;
  rr_powerplay: number;
  rr_middle: number;
  rr_death: number;
  rr_overall: number;
  sixes_per_match: number;
}

export interface Scores {
  accuracy: number;
  log_loss: number;
  brier: number;
}

export interface CalRow {
  bin: number;
  predicted: number;
  observed: number;
  n: number;
}

export interface WinProb {
  train_seasons: [number, number];
  test_seasons: number[];
  n_train_states: number;
  n_test_states: number;
  n_train_matches: number;
  n_test_matches: number;
  train_chase_win_rate: number;
  window_selection: { validation_season: number; chosen_start: number };
  model: Scores;
  model_without_scoring_level: Scores;
  baseline_constant: Scores;
  baseline_required_rr: Scores;
  coefficients: { intercept: number; weights: Record<string, number> };
  by_season: Record<string, Scores>;
  by_checkpoint: Record<string, Scores & { n: number; baseline_constant_accuracy: number }>;
  calibration: CalRow[];
  calibration_train: CalRow[];
  calibration_without_scoring_level: CalRow[];
}

export interface AccRow {
  n?: number;
  n_train?: number;
  n_test?: number;
  accuracy: number;
  accuracy_mean?: number;
  accuracy_sd?: number;
  predicts?: string;
}

export interface V1Comparison {
  labels: {
    matches_with_two_innings: number;
    no_result_counted_as_result: number;
    wrong_winner: number;
    ties_or_super_overs: number;
    dl_matches: number;
  };
  v1_as_written_2008_2022: AccRow;
  v1_as_written_all_seasons: AccRow;
  fixed_labels_still_leaky_random_split: AccRow;
  no_leakage_random_split: AccRow;
  corrected_season_holdout: AccRow;
  logistic_score_wickets_season_holdout: AccRow;
  baseline_majority_season_holdout: AccRow;
  test_seasons: number[];
}

export interface Summary {
  counts: {
    matches: number;
    decided: number;
    no_result: number;
    super_over_results: number;
    dl_results: number;
    deliveries: number;
    seasons: number;
    first_season: number;
    last_season: number;
    players_batted: number;
    raw_team_names: number;
    clean_team_names: number;
    raw_venue_names: number;
    clean_venue_names: number;
  };
  seasons: number[];
  season_summary: SeasonRow[];
  toss: {
    n_decided: number;
    overall: Binom;
    by_decision: { bat: Binom; field: Binom };
    decision_chi2: Chi2;
    by_era: Record<string, Binom>;
    era_chi2: Chi2;
    by_stage: { league: Binom; playoffs: Binom };
    chasing: Binom;
    chasing_by_era: Record<string, Binom>;
    effect_pp: number;
    mde_pp: number;
  };
  venue_toss: { venue: string; wins: number; n: number; rate: number; p_value: number; p_bonferroni: number }[];
  nrr_fit: { r: number; r2: number; slope: number; intercept: number; n: number };
  champions: { season: number; winner: string }[];
  aliases: { teams: Record<string, string>; venues: Record<string, string> };
  winprob: WinProb;
  v1_comparison: V1Comparison;
}

export interface TeamSeason {
  season: number;
  played: number;
  won: number;
  lost: number;
  no_result: number;
  win_pct: number | null;
  nrr: number | null;
  run_rate_for: number | null;
  run_rate_against: number | null;
}

export interface Team {
  name: string;
  short: string;
  active: boolean;
  titles: number[];
  alltime: {
    seasons: number;
    played: number;
    won: number;
    lost: number;
    no_result: number;
    win_pct: number;
    first_season: number;
    last_season: number;
  };
  seasons: TeamSeason[];
  top_batters: { batter: string; runs: number; balls: number; innings: number; strike_rate: number }[];
  top_bowlers: { bowler: string; wickets: number; balls: number; economy: number }[];
}

export interface H2H {
  team_1: string;
  team_2: string;
  matches: number;
  team_1_wins: number;
  team_2_wins: number;
}

export interface TeamsFile {
  teams: Team[];
  head_to_head: H2H[];
}

export interface VenueRow {
  venue: string;
  city?: string | null;
  matches: number;
  first_season?: number;
  last_season?: number;
  chase_win_pct: number;
  avg_first_innings: number;
  toss_winner_win_pct: number;
  field_first_pct: number;
}

export interface VenuesFile {
  all: VenueRow[];
  by_season: Record<string, VenueRow[]>;
}

export interface BatRow {
  batter: string;
  team: string | null;
  innings: number;
  runs: number;
  balls: number;
  strike_rate: number;
  average: number | null;
  sixes: number;
  sr_rank: number;
}

export interface ConsRow {
  batter: string;
  team: string | null;
  innings: number;
  runs: number;
  pct_25_plus: number;
  median_score: number;
  cv: number | null;
  strike_rate: number | null;
}

export interface BowlRow {
  bowler: string;
  team: string | null;
  balls: number;
  wickets: number;
  economy: number;
  dot_pct: number;
  balls_per_wicket: number | null;
}

export interface PlayersFile {
  thresholds: Record<string, number>;
  batting: Record<string, BatRow[]>;
  strike_rate: Record<string, BatRow[]>;
  consistency: Record<string, ConsRow[]>;
  bowling: Record<string, BowlRow[]>;
}

export interface AllData {
  summary: Summary;
  teams: TeamsFile;
  venues: VenuesFile;
  players: PlayersFile;
}
