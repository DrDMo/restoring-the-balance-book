# Restoring the Balance — study design (fixed before outcome analysis)

Volume 3, Shoreline Publishing Group Comparative Politics Series.
Working subtitle: *Authoritarian Demand and the Recovery of Democratic Constraint*.

Committed before any restoration outcome was linked to a covariate. Descriptive checks run before this commit:
reproduction of Vol. 2 quiet-erosion spells (65 spells, 53 non-provisional, 12 recovered; exact match).

## Question
Volume 1: demand (AGP) predicts autocratization onset. Volume 2: demand is weakly associated with sub-threshold
erosion; erosion rarely recovers (12/53). Volume 3: when democracies lose executive constraint, under what conditions
is it restored, in what order, and does restoration last? Is the return of constraint a demand-side process
(an ebb in AGP) or a supply-side one (elections, courts, parties, mobilization)?

## Units
**A. Backsliding episodes.** ERT v16 autocratization episodes with `aut_ep_prch == 1` (began in a democracy).
Episode end E = `aut_ep_end_year`. Pre-episode reference P = EDI (`v2x_polyarchy`) in the pre-episode year
(start year - 1). Trough = minimum EDI from start to E. Episodes ending 1950-2022 enter the restoration analysis;
episodes whose end is censored (`aut_ep_censored == 1` / outcome 6) are described but not at risk.
**B. Quiet-erosion spells.** The 53 non-provisional Vol. 2 spells, as reproduced (`spells.py`).

## Outcome: restoration (primary rule)
Episode restoration occurs in the first year t > E such that:
1. Magnitude: EDI(t) >= P - 0.05 (half the ERT cumulative threshold);
2. Credibility: EDI(t) > upper 68% bound of EDI at the trough year;
3. Regime: RoW `v2x_regime(t) >= 2`.
Time at risk: E+1 ... 2023; right-censored at 2023 or at the start of a new autocratization episode.
Alternatives (Ch. 12): tolerance 0.02 and 0.10; no credibility condition; restoration of half the loss
(EDI >= trough + (P - trough)/2); ERT democratization episode starting within 5 years of E (U-turn proxy).

Pathway restoration (A and B): on latent `v2x_veracc`, `v2x_horacc`, `v2x_diagacc`; a pathway "lost" if
P_i - min_i >= 0.15 over start..E; restored in first year t > E with index >= P_i - 0.075 (Vol. 2's recovery rule).

## Hypotheses and criteria
- **RB1 Asymmetry.** Restoration is slower than loss. Supported if (a) fewer than half of non-censored
  democratic backsliding episodes are restored within 10 years of E (Kaplan-Meier) AND (b) among restored
  episodes, median years E->restoration exceeds median episode duration (start->E).
- **RB2 Demand ebb.** Falling AGP raises the restoration hazard. Country-years at risk with two AGP waves at or
  before t: discrete-time logit of restoration on dAGP (most recent minus previous wave, standardized) with
  controls. Supported if coefficient < 0 and 95% CI (country-clustered) excludes zero. Secondary: AGP level < 0.
  Also tested on Vol. 2 spells (B).
- **RB3 Electoral reopening.** An election producing full executive turnover (`v2eltvrexo == 2`) after E raises
  the restoration hazard. Time-varying indicator "turnover election since E". Supported if coefficient > 0, CI excl. 0.
- **RB4 Vertical first.** Among episodes with >= 2 lost pathways that restore >= 2, vertical accountability is
  restored first (strictly earlier) more often than either other pathway. Supported if vertical-first share
  > 1/3 with a one-sided binomial p < .05 and vertical is the modal first pathway.
- **RB5 Institutional anchors.** Constraint retained at E raises restoration hazard: (a) judicial constraints
  (`v2x_jucon` at E) and (b) party institutionalization (`v2xps_party` at E). Supported per component if
  coefficient > 0, CI excl. 0; RB5 supported if both, partially if one.
- **RB6 Mobilization.** Pro-democracy mobilization (`v2cademmob`, lagged one year) raises restoration hazard.
  Supported if coefficient > 0, CI excl. 0.
- **RB7 Durability.** Restorations that also restore horizontal accountability are less likely to relapse
  (new autocratization episode starting within 10 years of restoration). Supported if relapse share is lower
  with horizontal restoration and the difference (Fisher exact, one-sided) has p < .05. Secondary: lower AGP at
  restoration associated with lower relapse (reported, power stated).

## Controls (all hazard models)
log GDP per capita (`e_gdppc`) at t-1; episode depth (P - trough); breakdown indicator (`aut_ep_outcome == 1`);
log years since E; decade of E. Errors clustered by country. Models: discrete-time logit; Cox (PHReg) as check.

## Power
State events and at-risk years for every model; report non-significant results with CIs, not as nulls proved.
