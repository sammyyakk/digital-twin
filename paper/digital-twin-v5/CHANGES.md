# Changes for revision round 2 (Yugnanda Ma'am's comments, 13 Oct 2026)

Base: `sammyyakk/digital-twin` main @ `9da054d` (16 Oct 2026), `paper/digital-twin-v4/main.tex`, copied into `paper/digital-twin-v5/` with the edits below.
Every number added comes from Samyak's answers (`paper/digital-twin-v5/SAMYAK_ANSWERS.md`,
`paper/digital-twin-v4/DHRITI_REVISION_V2.md`) or from his result files in `results/tables/`.
Nothing was rerun or estimated. The paper compiles with no errors and no overfull lines (17 pages).

---

## Part 1 — Changes made in `main.tex` and `supplementary.tex`

### D7. Title and "audited" / "validated"
- **Title:** "An Audited Multi-Horizon Evaluation with Validated Patient-Specific Insulin Sensitivity"
  → "An Integrity-Checked Multi-Horizon Evaluation with Stable, Dose-Consistent Patient-Specific Insulin Sensitivity".
- "audited" → "integrity-checked" in the abstract (Background), Contributions bullet 2, Fig. 1 caption and Conclusion.
- Fig. 1 final box: "Validated Patient Parameters" → "Patient-Specific Parameters".
- Sec. III-H heading: "…and Physiological Validation" → "…and Validity Checks".
- "Validated persistence baseline" kept (it means something different).

### D4 and D15. Abstract Results
- LOSO claim now gives the horizon: "under LOSO all 12 still beat persistence at 30 min by MAE (10 of 12 by RMSE)".
- Physics result now leads with the 5-seed mean ± SD: 30-min MAE 13.37 ± 0.11 vs 13.88 ± 0.25 mg/dL, 2.38 mg/dL lower at 120 min,
  Holm p = 0.002; the pre-specified single-seed test (13.25 vs 13.51, p = 0.105) follows. Source: Table VII.
- Abstract Methods: "checks tested the validity of S_I" → "checks tested whether S_I was subject-specific, stable, and dose-consistent".
- The provenance of 13.08 / 13.25 / 13.37 was already stated in the Table IV, V and VII captions; unchanged.

### D1 and D12. Effective sample size
- Sec. II-B: the 135,000 slots are now described as whole-cohort slots, noting that the 141,100 retained windows overlap and share them.
- Sec. II-B: added the test-set figures, 26,498/48 ≈ 552, or ≈ 494 with the 53.6-step autocorrelation time.
- Table III: row renamed "Effective independent windows, whole cohort (≈ 2,800)"; new row "Effective independent test windows ≈ 552 (≈ 494)".
- Sec. III-G1 (56 events): added that 56 events on ≈ 552 (494) effective test windows carry substantial uncertainty.
- Limitations: "…about 2,800 effectively independent observations, of which only about 550 fall in the test set; the hypoglycemia analysis rests on 56 events".

### D6. "Preregistered" → "pre-specified" (all 8 places)
- Sec. II-H heading, Table II caption, Sec. III-H text, Table XI caption, Sec. III-J (comparison), Limitations (two places), Appendix.
- Sec. II-H now opens: "The outcomes and criteria below were fixed on 25 July 2026, before any test-set evaluation."
  (Date from S8. The repo link and commit hash are not in the paper, as decided earlier; give them in the response letter.)

### D8 and D18. Insulin sensitivity wording and missing methods
- Table II row "S_I is externally consistent" → "S_I is dose-consistent".
- Sec. III-H: the dose relation is now called concurrent consistency, not external validity, with the reason
  (the parameter head sees the insulin inputs and TDD comes from the same records).
- Sec. III-H: added the ICC method (4 disjoint time-ordered blocks per subject, block medians, ICC(1) across subjects)
  and the TDD method (total recorded insulin ÷ recorded days, U/day). Source: S10.
- Circularity item 1: "not produced solely by the penalty" → "partly, but not solely, attributable to the penalty:
  removing it lowered ICC(1) from 0.890 to 0.645 and CV from 35.8% to 22.2%".
- Table XII group header "External Validation against Classic Minimal Model" → "Agreement with Classic Minimal Model".
- Body weight (Sec. III-H and Limitations): a fixed 70 kg is used for every subject for V_G, V_I and R_a. Source: S9.
- Limitations: "LOSO external validity fails" → "the dose relation fails under LOSO"; "external validity of one
  physiological quantity" → "stability and dose consistency of one physiological quantity".

### D13. Training time (Sec. II-I)
- "about 23 s per epoch (about 4.5 min per run)" → "Across the seven training runs reported here (A0–A4, A7 and the
  final quantile-head model), training stopped after 11–20 epochs (mean 16.3), at 10.7–23.8 s per epoch, or 2.7–6.4 min per run."
- Source: `results/tables/training_time_summary.csv`, **excluding** the `small-fast` run (see flag 1).

### D14. Quantile levels and CRPS
- Sec. III-G3: states that only q = 0.1, 0.5, 0.9 are trained, and that q = 0.05 and 0.20 come from a Gaussian
  left-tail extrapolation, with the formula. Source: S3.
- Sec. III-G4: states that CRPS is approximated from three quantiles, with the formula Samyak gave (see flag 2).

### D3. Upper quantile coverage (Sec. III-G4)
- Added: the q90 quantile is under-covered at every horizon (88.9%, 88.1%, 87.4%, 86.9% vs nominal 90%). Source: Table X.

### D2 and D16. PRED-EGA and Clarke A
- "exceeded 99.4%" → "at least 99.4%"; "stayed below 0.6%" → "at most 0.6%, reaching that value at 120 min".
- Next to the 99.96% acceptable claim: hypoglycemia-range Accurate is only 65.9% at 30 min, falling to 10.9% at 120 min (Table VIII).
- Clarke A 89.8% kept, now labelled as the final model's per-subject mean (Fig. 5). See flag 3.

### D11 and D21. Hypoglycemia, Tables VI vs IX
- "A7 had higher / more sensitive" → "numerically higher / numerically more sensitive", with 38 vs 33 of 56 events.
- Added subject-bootstrap 95% CIs (5,000 resamples): A7 [0.585, 0.750], A0 [0.453, 0.726], difference [−0.050, 0.235],
  which includes zero, so not significant. Source: S14.
- "physics does not degrade hypoglycemia detection" → "no evidence that physics degrades … but no significant improvement either".
- Table IX caption: same three CIs added.
- New paragraph: in the ablation, A7 was worse than A0 (0.608 vs 0.637; bias +8.61 vs +7.29); A0 swings 0.637 → 0.413
  once a quantile head is added; Tables VI and IX are different runs and should not be compared directly. Source: S15.

### D9 and D20. Baselines (Sec. III-C, Table V)
- Two rows added to Table V: ARX(6) + IOB/COB and Ridge (35 features), all horizons, MAE and RMSE ± SD.
  Source: `results/tables/extra_baselines.csv`. A7 is still lowest in every column.
- Model list: "nine models" → "eleven models", with the two new models described.
- "Linear models were competitive" replaced: AR(6) beats both non-mechanistic neural baselines at every horizon;
  the two new linear baselines match A0 at 30 min (13.56, 13.51), so most of the 30-min gain comes from the richer inputs;
  A7 is 0.26–0.31 mg/dL lower at 30 min, and 1.34 / 2.34 / 3.09 mg/dL lower than Ridge at 60 / 90 / 120 min;
  these differences were not tested for significance. See flag 6.

### D19. Ablation
- Sec. II-F: A7 "selected on validation data rather than the test set". Source: S11.
- Table VI: A4 label "Hybrid, fixed population parameters" → "Hybrid prior, curriculum, population parameters";
  caption adds "A3 and A4 differ only in per-patient parameterization; physics weighting and curriculum are held fixed". Source: S12.
- Sec. III-E1: Holm correction "across the four horizons, applied separately to MAE and RMSE". Source: S11.

### D5. Reference [8] (Cichosz et al.)
- "vol. 20, no. 3, pp. 836–847, 2024" → "vol. 20, no. 3, pp. 836–847, 2026 (published online 8 Oct. 2024), doi: 10.1177/19322968241286907".
- Volume, issue, pages, DOI and online date are from the article's ResearchGate record. See flag 9 for the print year.

### D17. Equation symbols
- Eq. 22: w_phys L_res → λ_phys L_phys; λ_pr → λ_prior, matching Eq. 17.
- Supplement loss table: L_res → L_phys, w_phys → λ_phys.

### D10. Comparators
- Table I footnote now points to Table XIII: "Stronger 2020 challenge entries (RMSE@30 of 17.45–19.05 mg/dL) are
  compared in Table XIII, where the current work is mid-field." (Numbers from Table XIII.)

### Fixes settled from Samyak's code (no new numbers)
- **Early stopping (Sec. II-I):** "validation MAE averaged across horizons" → "30-min validation MAE". The code
  (`twin/train/loop.py`) selects and stops on `val_mae_30`.
- **Final run (Sec. II-I):** added "The final quantile-head run stopped earlier, after 11 epochs, with its best
  validation MAE at epoch 3." Source: `results/tables/training_history.csv`. The reason is open (TODO_ROUND2.md S-1).
- **Subject-level S_I (Sec. III-H, flag 7 resolved):** "Each subject's S_I is the median of its window-level estimates;
  the between-subject CV and the dose correlation are computed across these 12 subject medians."
  Source: `twin/eval/sensitivity.py` (`s_i_median`).
- **Ablation Holm family (Physics Ablations, flag 5 resolved):** "Holm correction was applied across the five
  arm-versus-A0 comparisons (A1–A4 and A7) on 30-min MAE." Source: `twin/eval/results_doc.py`; check: 0.021 × 5 = 0.105.
- **A4 curriculum (flag 8 resolved):** `twin/train/ablations.py` shows A3 and A4 differ only in `per_patient_params`;
  both keep the default curriculum (only A7 removes it). The A4 label is correct.

### Layout
- The appendix still starts on a new page (page 15) with Table XIV on top; the conclusion stays on page 14.
  The page break now works whichever column the conclusion ends in, and the space around floats was reduced
  slightly (10 pt) so the conclusion fits on its page. 17 pages, no errors, no overfull lines.

---

## Part 2 — Flags: what is wrong or still open

**For Samyak**

1. **Training time (S2). Partly resolved.** His mean (16.4 epochs, 20.4 s/epoch, 5.5 min/run) includes `small-fast`, a run that is not
   in the paper (41 s/epoch, 11.7 min). The paper now uses only the seven paper runs. Also, the final quantile-head run
   stopped after **11 epochs**, but Sec. II-I says early stopping uses a patience of 12, which implies at least 13 epochs.
   Both his answer ("floor of 13") and Ma'am's premise conflict with this run. The results file shows the best epoch was 3,
   so it stopped after 8 epochs without improvement. The paper now states this fact; the reason is in TODO_ROUND2.md S-1.
2. **CRPS formula (S4). Open, TODO_ROUND2.md S-2.** His script says the formula was back-fitted to the existing numbers. 0.5·pinball_0.1 + pinball_0.5 + 0.5·pinball_0.9 reproduces the paper's values, but it is not
   the standard quantile approximation: integrating the pinball loss over quantile levels with the trapezoid rule gives
   weights 0.5 / 0.8 / 0.5 (8.43 instead of 9.74 at 30 min). The paper states his formula as used. He should confirm it is
   intentional, or recompute CRPS and Table X.
3. **Clarke A (S6).** His 89.86% is pooled across windows. Fig. 5 and the text use the per-subject mean, which for the
   final model is 89.80% (`summary_model.csv`). So the paper's 89.8% was already the final model's value; Ma'am's premise
   was mistaken. The paper keeps 89.8% and now labels it. Use this in the response letter.
4. **S8.** He said the commit is "already cited at main.tex:455". It was not: that paragraph was removed earlier. The paper
   now gives only the date (25 July 2026).
5. **Holm family for the ablation (S11). Resolved from code: 5 comparisons.** "4 horizons" fits the 5-seed test (0.00049 × 4 = 0.00195). The single-seed
   ablation result (p = 0.105) compares several physics arms with A0, so its family may differ. Not added to the paper; he must state it.
6. **New baselines (S13).** His conclusion "only ~0.3 mg/dL gap remains" holds at 30 min only. At 60–120 min A7 is
   1.3–3.1 mg/dL better than Ridge. The paper states this horizon by horizon. No significance test exists for A7 vs Ridge or ARX+IOB/COB.
7. **Subject-level S_I (S10). Resolved from code: median of window estimates.** He described the ICC blocks, but not how the single per-subject S_I used for CV and the
   dose correlation is obtained (median of all windows?). Only the ICC method was added; he must confirm the rest.
8. **A3 vs A4 (S12). Resolved from code: same curriculum.** His code check says they differ only in per-patient parameters, so the A4 label now says "curriculum".
   He should confirm A4 really uses the same curriculum as A3, because the label now states it.

**For Dhriti**

9. **Reference [8] print year.** The record gives vol. 20, no. 3 and online publication on 8 Oct 2024, but not the print year.
   2026 was inferred from the journal's volume numbering (vol. 1 = 2007). Check the issue year on the journal site; if you
   would rather not rely on it, cite the online-first form instead ("2024, doi: …" without vol./no./pp.).
10. **Comparators [11] and [68] (D10, partly done).** Only the pointer from Table I to Table XIII was added.
    - [68] Gu et al. (EMBC 2020): their lab page reports OhioT1DM, 6 subjects, 30-min RMSE 17.80 mg/dL (no MAE, no 60 min),
      but not which cohort (2018 or 2020). Check the paper's dataset section, then add the row to Table I.
    - [11] Wang et al. (DDCLS 2025): paywalled; dataset unknown. Check via college IEEE access; add a row if it reports
      official-split OhioT1DM results, otherwise add a footnote saying why it is omitted.
11. **Response letter.** Explain the points where the reviewer's premise was not quite right: Clarke A (flag 3) and A3/A4 (flag 8).

---

## Part 3 — Round 2 follow-up (after `SAMYAK_ANSWERS_ROUND2.md`, commit `c574437`, 17 Oct 2026)

### Applied in `main.tex`
- **CRPS (S-2).** Table X CRPS column 9.74 / 16.18 / 20.85 / 24.32 → **8.43 / 13.99 / 18.02 / 21.01** mg/dL.
  Sec. III-G4 sentence now gives the method: twice the trapezoidal-rule integral of the pinball loss over
  τ ∈ {0, 0.1, 0.5, 0.9, 1}, loss zero at τ = 0 and 1, i.e. 0.5·pinball_0.1 + 0.8·pinball_0.5 + 0.5·pinball_0.9.
  Source: `results/tables/calibration_by_horizon.csv`. Checked by hand: 0.5·2.976 + 0.8·6.532 + 0.5·3.441 = 8.434.
- Paper still compiles with no errors or overfull lines, 17 pages, appendix still starts on page 15.

### Not applied (see `TODO_ROUND3.md`)
- **S-4 (Tables V and VI).** The harmonized values would put across-seed SDs in a table captioned "SD across
  subjects", make Tables V and VI disagree on A0/A7 MAE, and leave Table VI's hypoglycemia column mixing
  quantile-head values (A0, A7) with old unreproducible values (A1–A4).
- **S-1 (early stopping).** Samyak's diagnosis (selection starts at epoch 26, nothing selected) assumes the
  default curriculum. The final run used the A7 configuration (`physics_ramp = 1.0` at epoch 1 in
  `training_history.csv`), so selection was active from epoch 1. The saved checkpoints must be checked
  before deciding on a rerun.
- **S-3** needed no paper change.

## Part 4 — References (20 Oct 2026, from the PDFs of [8] and [68])
- **Ref [8] (Cichosz et al.):** print year confirmed as 2026, vol. 20, no. 3, pp. 836–847 (Aalborg University
  accepted-manuscript record). No change needed.
- **Ref [68] (Gu, Dang & Prioleau, EMBC 2020):** Table I gets a new first row in the non-physics group:
  "Neural physiological encoder + LSTM", RMSE@30 17.80, other columns not reported. Source: Table V of their
  paper (OhioT1DM subjects 559–591, i.e. the 2018 cohort, official split). The footnote now lists [35] and [68]
  as the 2018-cohort exceptions.
- **Sec. III-E wording:** "earlier physiology-informed OhioT1DM studies [35], [68]" → "earlier physiology-based [35]
  and physiology-inspired [68] OhioT1DM studies", because [68] uses no physiological equations.
- Still 17 pages, no errors or overfull lines, appendix on page 15.
- **Still open:** ref [11] (Wang et al., DDCLS 2025).

## Part 5 — Ref [11] removed and citation numbers fixed (20 Oct 2026)
- **Ref [11] (Wang, Zhang & Song, DDCLS 2025) removed.** Full text not available to verify what the paper says
  about it. Removed its one citation, the Sec. I-B sentence "Bergman-constrained PINN models tied the network
  explicitly to the Bergman minimal model, ... dataset-specific [11]", and its reference entry. The Sec. I
  sentence "validation has typically remained simulator-only or narrowly dataset-specific [10]–[11]" now reads
  "some of these models were validated only in simulation [10]". The paper now has 74 references; everything
  after the old [11] moves down by one (old [68] Gu et al. is now [67]).
- **Hard-coded citation numbers fixed (existing bug since v4).** 33 citations in the paper are written as
  fixed numbers (`\hyperref[...]{N}`) rather than `\cite`, so they do not renumber automatically. When the
  preregistration reference was removed in v4, 17 of them were left one too high: for example the meal-model
  sentence printed [44]–[46] for references 43–45, and the 2020 challenge comparison printed [70]–[73] for
  69–72. All 33 now match the reference list (checked by script).
- Still 17 pages, no errors, overfull lines or undefined references; appendix on page 15.

## Part 6 — Table I cohort column (20 Oct 2026)
- **New "Cohort" column** in Table I: 2018 for [34] Bertachi and [67] Gu, 2020 for all other studies.
- **New rows** so each study has a same-cohort comparison: "Current Work (same model)" on the 2018 cohort
  (RMSE/MAE 18.93/12.92, 29.89/21.42, 37.69/27.70, 43.53/32.44 at 30/60/90/120 min) and persistence on the
  2018 cohort (22.52/16.28, 36.19/26.92, 46.22/34.76, 53.89/40.97). Existing current-work and persistence rows
  are labelled 2020.
- Source: means of the six 2018 subjects in `results/tables/per_subject_model.csv` and
  `per_subject_persistence.csv`. The same files reproduce every existing 2020 value in Table I exactly, and the
  2018 persistence values (22.52, 36.19) match Sec. II. Nothing was rerun.
- Footnote: the 2018 exception sentence is replaced by "The Cohort column gives the six-subject OhioT1DM test
  cohort (official split) on which each result was reported; values are comparable only within a cohort, so
  the current work and persistence are reported separately for each."
- On the 2018 cohort the current work beats [34] (18.93 vs 19.33 at 30 min; 29.89 vs 31.72 at 60 min) and is
  behind [67] (18.93 vs 17.80 at 30 min). For the response letter: [67] fills missing test CGM values by
  extrapolation, whereas this paper scores only real readings.
- Still 17 pages, no errors or overfull lines, appendix on page 15.

## Part 7 — 2018-cohort comparators (20 Oct 2026)
- **Removed [67] Gu et al.** (EMBC 2020): its Table I row, its citation in Sec. III-E (sentence now cites only
  [34]: "an earlier physiology-based OhioT1DM study that primarily reported forecast accuracy"), and its reference entry.
- **Added three 2018-cohort journal studies to Table I** (non-physics group, sorted by RMSE@30), values read
  from each paper:
  - GluNet: K. Li et al., IEEE J. Biomed. Health Inform. 24(2):414–423, 2020. 6 OhioT1DM subjects, challenge
    split. RMSE 19.28 ± 2.76 (30 min), 31.83 ± 3.49 (60 min) (their Table IV). No MAE (MARD reported instead).
  - H. Nemat et al., Sci. Rep. 14:21863, 2024. Ohio_2018, last 10 days as test. Best model (SVR,
    multivariate) average RMSE/MAE 19.59/13.49 (30 min) and 31.54/22.86 (60 min) (their Tables 4 and 5).
  - GLYFE: M. De Bois et al., Med. Biol. Eng. Comput. 60(1):1–17, 2022. Subjects 559–591, the "traditional
    testing set" (last 10 days). Best model (Gaussian process) RMSE 20.01 (30 min), 31.97 (60 min),
    46.24 (120 min) (their Table II). No MAE.
- All three fill missing test CGM values by extrapolation (GLYFE, Nemat) or do not say (GluNet).
- Bib entries inserted after [34], so they are [35]–[37]; every hard-coded citation number re-checked by script.
- CRPS sentence (Sec. III-G4) shortened to keep the Conclusion on page 14; same formula and values.
- Still 17 pages, no errors, overfull lines or undefined references; appendix on page 15.

## Part 8 — Table I harmonized with Table XIII (20 Oct 2026)
Answers Ma'am's comment: "Table I shows only weaker 2020 entries ... Table XIII adds stronger ones ... Harmonize
them, and add or explain [11], [68]." Table I keeps the same number of rows (17 studies + [34]).
- **Added to Table I** (values copied from Table XIII, which the paper already had): CNN/LSTM 17.45,
  N-BEATS + BiLSTM 18.22, LSTM 18.23, NN-EIM 18.63, MS-LSTM 19.05 (all 2020). Table I and Table XIII now
  show the same 2020 entries.
- **Gu et al. ([68] in Ma'am's numbering) restored** as a 2018 row (17.80), classed as non-physics because
  it uses a learned neural encoder, not physiological equations. Reference entry restored with DOI.
- **Removed from Table I:**
  - Four 2018 workshop rows that were added to `main.tex` outside these edits and could not be verified:
    Chen et al. 19.04 (published value 18.9), Xie & Wang 19.53, Martinsson et al. 20.10, Zhu et al. WaveNet 21.73.
    Their now-uncited reference entries (Chen, Zhu) were removed. Martinsson and Xie & Wang stay in the reference
    list because they are cited in Sec. II-A as persistence baselines.
  - Two duplicates of studies already in the table: the single-task ablation of the multitask CRNN, and the
    second variant of the multi-class LSTM.
- Rows in the non-physics group are sorted by RMSE@30, so the current work's position is visible.
- **Footnote:** "Stronger 2020 challenge entries (17.45–19.05) are compared in Table XIII, where the current work
  is mid-field" → "The current work is competitive with published results on both cohorts; Table XIII also
  compares the 2020 entries with its LOSO results."
- 77 references; all hard-coded citation numbers re-checked. Still 17 pages, no errors; appendix on page 15.
- **Table I footnote rewritten** for reviewers (four sentences): cohort subject IDs (2018: 559–591; 2020:
  540–596) and comparability only within a cohort; some studies score against interpolated/extrapolated test
  values while the current work uses only recorded CGM readings; meaning of "not reported"/–; pointer to
  Tables IV and XIII for all-subject and LOSO results. Ranking is left to the sorted table and Sec. III-J.

## Part 9 — Supplement title (20 Oct 2026)
- `supplementary.tex` still had the old title ("An Audited Multi-Horizon Evaluation with Validated Patient-Specific
  Insulin Sensitivity"); now matches `main.tex`.

## Part 10 — Samyak's round-3 answers (25 Oct 2026)
Base: `sammyyakk/digital-twin` main @ `6251c44`.
- **S-7 (Sec. II-I):** added the selected configuration: "validation selected 2 layers, d_model = 64, 4 heads,
  d_ff = 128, dropout 0.2, attention pooling, and Kendall weighting." Source: `configs/official-small.yaml`,
  confirmed by Samyak.
- **S-6 (Sec. III-H, Table XII):** after the ρ = 0.790 sentence: "This reference is weak (30-min MAE 25.5 mg/dL
  even on training data), so agreement indicates only loose convergent validity." Table XII interpretation
  "Agreement" → "Weak reference" for the two Bergman rows. Source: `results/tables/bergman_insample_fit_quality.csv`.
- **Sec. III-J (D-5, partly):** "differ slightly from the 2020-cohort figures in Tables I and XIII; both are
  correct, answer different comparability questions, and should not be averaged together" → "differ from the
  per-cohort figures in Tables I and XIII because they answer a different comparability question" (Table I
  now has 2018 rows).
- **Not changed:** Sec. II-I early-stopping sentence (S-1 follow-up open) and Table VI (S-4 still open).
- Still 17 pages, no errors; appendix on page 15.

## Part 11 — Dhriti's items D-4, D-5, D-6, D-8 (25 Oct 2026)
- **D-4 Title** (main and supplement): "...with Stable, Dose-Consistent Patient-Specific Insulin Sensitivity" →
  "...with a Stable Patient-Specific Insulin-Sensitivity Estimate".
- **D-5 Comparison:**
  - Zhu et al. GAN [2020 cohort, subjects 540–596] added to Table I and Table XIII: RMSE/MAE 18.34/13.37 (30 min),
    32.21/24.20 (60 min), from Table 1 of their paper. Table I keeps its length: Seq2Seq BiLSTM (21.80, weakest
    row, cited nowhere else) removed with its reference entry.
  - Sec. III-J: "Further 2020 entries report RMSE@30 of 18.34 and 19.60" → "A further 2020 entry reports RMSE@30
    of 19.60 mg/dL [Joedicke]" (Zhu GAN is now in the tables and added to the mid-field citation list).
  - Sec. III-J: "MAE (22.55) is lower than every entry except one whose MAE-to-RMSE ratio is far outside the range
    of the other entries [Pavan]" → "MAE (22.55) is the second lowest".
  - Table XIII kept: it is the only place with the LOSO row for the 2020 cohort.
- **D-6 Wording:**
  - Fig. 4 caption: now says the 5-seed replication (13.37 vs 13.88 mg/dL) found A7 significantly better.
  - Abstract conclusion: "In this cohort, calibrated predictive tails, not error-grid scores, determined
    hypoglycemia detection."
  - Sec. III-G1: "At about two false alarms per day, alarm fatigue is a concern [Shivers et al., J. Diabetes Sci.
    Technol. 7(3):789–794, 2013], so the operating point would need to be set with patients." New reference.
- **D-8 Fig. 7:** feature names now readable (e.g. "Rate of change (5 min)", "Time since bolus"); caption says
  "the 5-min glucose rate of change" instead of the code name.
- **Space:** to stay at 17 pages, three figure captions were shortened, each dropping a sentence that repeats the
  text: Fig. 2 ("...gap between them widens"), Fig. 3 (last clause), Fig. 5 (last sentence) and Fig. 7 (last sentence).

### Correction to Part 5 (citation numbers)
Part 5 said 17 hard-coded citation numbers had been wrong since v4. That was a mistake in my checking script:
it ignored the reference with a non-numeric key (`refBH`), so it miscounted. The v4 numbers were correct, and the
"fix" made them one too low for 17 citations (e.g. the meal-model range and the 2020-challenge range). That version
went into PR #12. All hard-coded numbers are now checked against every reference entry and are correct.

## Part 12 — Author name and ref [11] (25 Oct 2026)
- Author line: "Yugananda Malhotra" → "Yugnanda Malhotra" (matches her email).
- Ref [11] (Wang et al., Tsinghua Sci. Technol.) completed from the publisher page: "vol. 32, no. 1, pp. 549–561,
  2027 (published online 2026), doi: 10.26599/TST.2025.9010140" (was "2026" only). Year to confirm (D-13).
- Still 17 pages, no errors; appendix on page 15.

Open items from here on are in `TODO_ROUND4.md`.

## Part 13 — Samyak's round-4 answers (26 Oct 2026)
Base: `sammyyakk/digital-twin` main @ `15246ad`.
- **S-1 (Sec. II-I):** "early stopping after 12 epochs ... The final quantile-head run stopped earlier, after 11
  epochs, with its best validation MAE at epoch 3" → patience 10 (ablation arms, 5-seed runs), 12 (quantile-head A0),
  8 (final model, best epoch 3 of 11). Added the validation split (final 15% of each subject's time-ordered training
  windows, purge gap of one input window plus the longest horizon) and LOSO selection. Source: Samyak's checkpoint table.
- **S-4 (Table VI, Sec. III-G2):** hypo sensitivity 0.637/0.502/0.499/0.485/0.517/0.608 → 0.621/0.488/0.486/0.471/
  0.504/0.591 (A0–A4, A7). Bias unchanged (reproduces exactly). Text: "0.608 vs 0.637" → "0.591 vs 0.621";
  "fell from 0.637" → "fell from 0.621". Source: `results/tables/table_vi_hypo_corrected.csv`.
- **S-9 (Sec. III-E1):** subject-bootstrap 95% CIs for the A7 − A0 MAE difference, [−0.70, −0.36] at 30 min to
  [−3.15, −1.69] at 120 min. Source: `results/tables/physics_effect_cis.csv`.
- **S-10 (Sec. III-G4):** split-conformal recalibration restores marginal coverage (82.3% at 30 min, 79.5% at 120 min)
  but not coverage below 80 mg/dL (78.1%, 51.9%). Linear quantile-regression baseline: CRPS 8.54–22.75, width
  43.8–114.0 mg/dL. Sources: `conformal_recalibration.csv`, `conformal_low_glucose_coverage.csv`, `probabilistic_baseline.csv`.
- **"Calibrated" softened:** abstract conclusion ("lower predictive quantiles ... although coverage below 80 mg/dL
  remained poor"), Discussion and Conclusion.
- **Not applied:** the hypoglycemia alarm baseline. Its thresholds were tuned on the test set (S-11 rerun).
- **Fixed (my error in Part 11):** the Sec. III-J citation range printed "[71-, [75]74]"; now "[71–74], [75]".
- Still 17 pages, no errors; all hard-coded citation numbers checked.

## Part 14 — Dhriti's items D-9 to D-12 (26 Oct 2026)
- **D-9 (Sec. I):** removed the "parallel tracks" paragraph and the digital-twin review sentence; the six-sentence
  digital-twin/RCT paragraph is now one sentence (refs [13]–[18] kept). New paragraph after the three open questions:
  this work does not propose a new physiological model; its contribution is the combination of (i) real-CGM-only
  targets at verified horizons with subject-level analysis, (ii) a pre-specified ablation and multi-seed test,
  (iii) pre-specified checks of S_I, and (iv) quantile forecasts evaluated for hypoglycemia under both protocols.
  Third open question: "calibrated predictive distribution" → "predictive distribution".
- **D-10:**
  - Abstract: "In a post hoc five-seed replication on the same test set, ..."; conclusion "small but consistent
    accuracy gains" → "small accuracy gains in a post hoc replication".
  - Sec. III-H: "Ambient glucose" → "Mean glucose". Sec. III-I: "showing that physiology-derived inputs are
    informative in their own right" → "suggesting that physiology-derived inputs carry information, although
    attributions among correlated features should be read with caution".
  - Discussion: the 0.51–2.38 mg/dL gain is about 4% of MAE at 30 min (unlikely to change a clinical decision on its
    own) and about 7% at 120 min.
  - Limitations: the evidence for S_I is internal (stable and dose-consistent within this cohort, weak external
    reference); no clamp; dose relation fails under LOSO; usefulness for insulin dosing untested.
  - Conclusion: "In this 12-subject cohort, an integrity-checked ... forecaster outperformed ...".
  - Sec. III-J: "calibrated hypoglycemia detection" → "lower-quantile hypoglycemia detection".
- **D-11:** Table II has an "Outcome" column: beats persistence, met (12/12); field-competitive, met (13.08 final,
  13.37 5-seed); physics improves accuracy, not met (Holm p = 0.105; significant only post hoc); S_I CV, met (35.8%);
  ICC, met (0.890); dose consistency, met official (ρ = −0.839), not met LOSO.
- **D-12:**
  - Sec. II-B: "...so results are compared only within a cohort."
  - Table XIII removed: its entries were all in Table I. Sec. III-J now gives the 2020-cohort LOSO result
    (20.93/14.98 mg/dL at 30 min) and the 2018 position (RMSE@30 18.93, lower than four of five 2018 entries, above
    Gu et al. 17.80). Table XIV (parameter vector) is now Table XIII.
  - Table I footnote: "All-subject results: Table IV. Most comparators are BGLP challenge workshop papers."
  - Captions shortened: Table IV (one line), Table VI and VII (explanations removed; they are in the text), Table IX
    (CIs removed from the caption; they are in Sec. III-G2).
- Still 17 pages, no errors or overfull lines; appendix on page 15; 78 references, all cited, all hard-coded
  numbers correct.

## Part 15 — Full cross-check against the result files (26 Oct 2026)
Checked against `sammyyakk/digital-twin` main @ `15246ad` (`results/`, `paper/digital-twin-v5/data/`):
- **Match:** abstract numbers; Table IV (all values, skill, 12/12 subjects, 12.2–31.6% skill range); Table V (every
  cell) and the Sec. III-C differences; Table VI MAE and Clarke A; "9 of 12 subjects"; Table VII and Wilcoxon/Holm;
  Table IX (except A0 event specificity, S-17); Table X and calibration text; window counts (187,780 / 141,100 /
  36,395 / 10,285 / 26,498); autocorrelation time 53.6; LOSO claims (12/12 by MAE, 10/12 by RMSE, about 12% vs
  persistence, gap 1.6–4.3 mg/dL) and the 2020 LOSO values; S_I statistics (CV, ICC, ρ, CIs, no-λtc ablation,
  partial correlations for test-interval glucose, Bergman agreement, ICR, gate values); attribution shares, the
  3.11 mg/dL top feature and "over seven times"; Clarke A+B and Parkes A+B; Fig. 6 values (CV ratio, LBGI, TIR,
  TBR); Table I current-work and persistence rows.
- **Fixed:** Fig. 5 caption said Clarke zones D and E "remain negligible"; zone D reaches about 5% at 120 min.
  Now: "zone D rises from about 1% to about 5%, and zone E stays below 0.05%".
- **Flagged for Samyak:** S-15 (A0 handicap in the 5-seed replication), S-16 (Table VIII mismatches),
  S-17 (numbers with no result file).

Open items from here on are in `TODO_ROUND5.md`.

## Part 16 — Ref [11] year (26 Oct 2026)
- Ref [11]: "2027 (published online 2026)" → "2027", as confirmed by Dhriti (D-13 done).

## Part 18 — Round 6: Samyak's re-evaluation (`DHRITI_ROUND6.md`) applied (26 Oct 2026)
Base: `sammyyakk/digital-twin` main @ `c699992`; `main.tex` from `247c1b8`, as `DHRITI_ROUND6.md` assumes. The
round-5 edits made on 26 Oct afternoon (never pushed) are superseded: the round-5 "A0 detects more events" result was
one seed with unequal patience (12 vs 8), and the five-seed replication (P9) replaces it.
- **All sections of `DHRITI_ROUND6.md` applied as written:** abstract (methods sentence, physics and cross-cohort
  results, persistence-alarm sentence, conclusion); contributions bullets 3 and 5; new paragraph on the secondary
  analyses in Sec. II-H (label `sec:prespec`); Table II physics outcome; new Sec. III-D2 "Cross-Cohort Transfer" with
  Table VI and a figure; Sec. III-E and Fig. 4 caption (0.17/0.99 mg/dL); Table VIII (five-seed) rows, header and
  caption; the post-table paragraph and "Where the gain arises"; Table IX PRED-EGA and "0.14% at 60 min"; Sec. III-G
  (five ways, persistence and linear-extrapolation alarms, five-seed A0 vs A7 paragraph, old A0 rows removed from
  Table X with the two baseline rows added, new Table XI five-seed alarm table, III-G3 renamed "Alarm Operating Curves"
  with the F2 analysis removed); partial correlations restored with −0.885 and the method note; attribution
  ρ = 0.740; Discussion, Limitations and Conclusion.
- **Supplement:** new Table S6 (secondary analyses P1–P5 and P7, all 47 rows, from `round6_all_tests.csv`) and Table S7
  (P6 low data, from `round6_p6_lowdata.csv`), plus the P5 robustness sentence (0.10% vs 0%).
- **Additions not in `DHRITI_ROUND6.md`:**
  1. Novelty point (iv) said hypoglycemia was evaluated under LOSO; it was not. Now: "quantile forecasts whose
     hypoglycemia alarms are compared with a simple persistence alarm, and point accuracy reported under both
     personalized and leave-one-subject-out protocols".
  2. Sec. III-J: "The defensible advances are lower-quantile hypoglycemia detection" → "an evaluation of hypoglycemia
     alarms against a simple baseline" (the persistence alarm matches the quantile alarm).
  3. "Where the gain arises": added "In that family the overall gaps themselves did not survive correction
     (Holm p = 0.07–0.35), so these strata indicate where the effect lies rather than add independent evidence for it."
     (Table S6 P1 rows show this; without the sentence, the main text and Table S6 look contradictory.)
  4. Main text pointed to "Table S1"; the supplement already had S1–S5, so the new tables are S6 and S7. Supplement
     references updated to Table VIII (five-seed) and Table XV (parameter vector) after renumbering.
- **Checks:** no compile errors or overfull lines; all 78 references cited with correct numbers; none of `84.0`,
  `0.771`, `3,397`, `0.886`, `0.731`, `13.88`, `0.00195`, `0.413`, `0.861`, `reduced variability` remain. Key numbers
  checked against `round6_hypo_multiseed.csv`, `round6_external_summary.csv`, `si_partial_corr_regen.csv`,
  `round6_all_tests.csv`, `f2_threshold_regen.csv`.
- **Length:** 19 pages (was 17). Page 16 holds only the parameter table and the last 10 lines of the Conclusion.
  Removing the cross-cohort figure (its numbers are all in Table VI) gives 18 pages with no blank page.
- **Final cross-check fixes (26 Oct, after a full number check against the result files):**
  1. Discussion: cross-cohort gain "about 9--16%" -> "about 9--17%" (largest is 16.6%, 2020->2018 at 90 min).
  2. Abstract conclusion: "gains that grew with horizon" -> "gains that were larger at longer horizons"; Sec. III-E1
     now adds that the pre-specified trend test (P1) was not significant after Holm correction (p = 0.17).
  3. Abstract methods: "specified before they were run" -> "planned after the main results but before being run"
     (matches "post hoc" in Results and Sec. II-H).
  4. Discussion: "most clearly, under distribution shift" -> "most consistently" (no cross-cohort test survived Holm).
  5. Limitations: seed-variability sentence now ends "(not significant)" (P7, Holm p >= 0.64).
- Fig. (feature attribution), permutation panel: feature labels switched from monospace to the normal font (31 Oct).
- Abstract shortened (31 Oct), 485 -> 413 words (S_I and alarm sentences then reworded for clarity). Methods: "Secondary analyses, planned after the main results but
  before being run, replicated..." -> "Post hoc secondary analyses replicated...". Results rewritten from 215 to 130
  words; same findings and numbers, dropped: RMSE at each horizon (now a 30-120 min range), the single-seed 30-min MAEs
  and five-seed 30-min MAEs (now the 0.17-0.99 range), the attribution sentence, and the alarm precision 0.347.
- Abstract rewritten to under 300 words (31 Oct): 413 -> 290 words (296 counted from the PDF). Same findings; dropped
  the per-horizon RMSE values and 18.84 headline (now "19.4-21.2% lower RMSE than persistence at 30-120 min"), the
  Wilcoxon/Holm detail in Methods, the low-glucose coverage clause in the Conclusion, and shortened every sentence.
  Side effect: the paper is now 18 pages; the Conclusion ends on p15 and the appendix starts on p16, no blank page.
- Abstract "Background and objective" rewritten (31 Oct): "Glucose dynamics in type 1 diabetes are nonlinear,
  delayed, and patient-specific, driven by meals and insulin. This study develops a physics-guided probabilistic
  forecaster that combines deep sequence learning with mechanistic physiological modeling, and tests what the physics
  adds beyond accuracy under an integrity-checked protocol." To stay under 300 words, Methods/Results/Conclusion
  lightly trimmed (absorption-state clause removed, post hoc sentence shortened). Abstract now 293 words.
- Abstract Conclusion rewritten to state the contribution (31 Oct): "Unlike evaluations of physics-guided forecasters
  based on accuracy alone, this study shows what physics adds: a stable insulin-sensitivity estimate, dose-consistent
  under personalized evaluation, and small accuracy gains that grow under cross-cohort transfer, but no better
  hypoglycemia detection than a tuned persistence alarm."
- Sec. III-G3: file path "(data/sensitivity_precision_curves.csv)" replaced by "(in the code repository)" (31 Oct).
- Code names removed from the text (31 Oct): Sec. II-H "(PREREG_ROUND6.md in the code repository)" -> "(the record is in the code repository)"; Sec. III-H "(abl-A7-notc)" removed.
- Introduction novelty point (ii) now includes the cross-cohort transfer test, matching contribution bullet 3 and the abstract conclusion (31 Oct).
- Contribution bullet 1 reframed (31 Oct): "...delivering 30, 60, 90, and 120-minute glucose forecasts that consistently outperform a validated persistence baseline" -> "...for 30--120-minute glucose forecasting, as the basis for testing what physiological structure adds".
- Final worst-case check (31 Oct). Sec. II-I training details: removed "12 for the quantile-head A0" (that single-seed
  run is no longer reported; the five-seed alarm runs use patience 10, per scripts/run_seeds_a0_a7.py), now "patience
  10 for the ablation arms and all multi-seed and secondary-analysis runs, and 8 for the final quantile-head model";
  Sec. II-J "seven training runs reported here" -> "seven primary training runs" (the paper now reports more runs).
  Also re-derived from results/tables/per_subject_*.csv and results/loso/per_subject_loso.csv: Table I rows for this
  work and persistence (both cohorts, all horizons), Sec. III-K comparison claims, MAE skill range 12.2-31.6%,
  LOSO 12/12 (MAE) and 10/12 (RMSE): all match.
