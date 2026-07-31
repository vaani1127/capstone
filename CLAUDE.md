# HealthSaathi — Project Context for Claude Code

Read this fully before doing anything. This file exists because the project has
been audited and partially fixed across an earlier chat session with a
different Claude instance, and continuity matters — don't re-fabricate
things that were already caught and fixed once.

## What this project is

Mobile-first Hospital Management System (HMS) capstone for small/mid-sized
Indian clinics. Solo-built by Vaani (B.Tech capstone; two teammates had scoped
roles that didn't materialize into code — the "5 people" framing is about
final polish/presentation quality, NOT about fabricating authorship. Never
write anything that claims specific people did specific work they didn't do.)

**Stack (do not change without an explicit, strong reason):** FastAPI +
PostgreSQL backend, Flutter mobile frontend, SQLAlchemy + Alembic, JWT/RBAC
(Admin/Doctor/Nurse/Patient), WebSocket real-time alerts, SHA-256 hash-chain
audit trail, IsolationForest + SHAP anomaly detection, Docker.

**Repo:** https://github.com/vaani1127/capstone (public)

## Hard rules — read before touching anything

1. **Never invent numbers.** This project already had a serious problem with
   AI-generated documentation containing fabricated metrics (99.9% uptime,
   500+ req/sec, 1000+ concurrent users, "50,000+ lines of code" — none of
   this was ever measured). All of that was found and removed. If you don't
   have a number from an actual measurement (grep count, benchmark output,
   test run), either don't state it or clearly label it as an estimate.
2. **Verify claims against the actual code**, not against what a previous doc
   or comment says. Prior docs have been wrong before (e.g. claimed 14 DB
   models, actual is 13; claimed vague "3-5 req/min per endpoint" rate
   limiting, actual is only 2 of 54 endpoints are limited: login 5/min,
   register 3/min).
3. **Don't do a tech-stack rewrite.** Explicitly decided against this. Only
   add/fix what's feasible within the current stack.
4. **The novelty angle is deliberately NOT "we used IsolationForest+SHAP."**
   That specific combo is a saturated pattern in 2024-2026 EHR anomaly
   detection literature — multiple papers do this exact thing. It is NOT
   defensible as novel on its own. See "Novelty framing" section below for
   what actually is defensible.

## Verified current state (as of last audit)

- 13 database models, 54 API endpoints (both counted directly from code)
- 11 Alembic migrations (008-011 chain specifically verified clean; an
  earlier `create_all()` bypass bug was found and fixed)
- Rate limiting: ONLY `/auth/login` (5/min) and `/auth/register` (3/min) have
  `@limiter.limit()` decorators. No other endpoint is rate-limited.
- Test suite: 8 files, 133 test functions total (test_auth 14, test_appointments
  23, test_medical_records 18, test_blockchain 20, test_anomaly 18,
  test_behavioral_score 13, test_fallback_explanation 14, test_read_audit 13)
- Tamper-detection hash-chain benchmark: 100% detection across 27 trials,
  O(N) latency scaling — see `benchmark_tamper_detection.py` at repo root.
  This is a genuinely rare thing to have actually benchmarked; most papers
  propose tamper-detection schemes without measuring detection latency.
- ~22,600 lines of code (backend `app/` + mobile `lib/`, via `wc -l`,
  excludes tests/migrations) — NOT "50,000+" as an earlier doc falsely claimed.

## What's already been done (don't redo, verify if unsure)

- [x] Fixed 3 fatal bugs in synthetic audit-log dataset generation (100%
      anomaly rate, inverted off-hours flag, only 60-day span)
- [x] JWT logout blacklist wiring in Flutter — clears local token/prefs even
      if the backend call fails (`services/auth_service.dart`)
- [x] 429 rate-limit interceptor in Flutter — surfaces the real `Retry-After`
      header instead of a hardcoded string (`services/api_client.dart`)
- [x] NO_SHOW appointment status — Flutter model getter, "Mark No-Show" button
      (only shown for `scheduled` status, matching the backend's
      SCHEDULED-only transition restriction), status chips across
      doctor/nurse/admin screens
- [x] Behavioral-scores feature — this needed BOTH a new backend endpoint
      (`GET /anomaly/behavioral-scores/{user_id}`, previously didn't exist at
      all) and a new Flutter screen (`behavioral_score_trend_screen.dart`).
      The endpoint's `sustained_trend_flagged` logic imports `TREND_WINDOW`
      and `TREND_THRESHOLD` directly from `anomaly_service.py` rather than
      duplicating the constants — keep it that way so the UI and the actual
      alerting logic can never disagree.
- [x] Fixed stale duplicate `project/requirements.txt` (was missing
      scikit-learn/shap/slowapi/bleach; now points to the real
      `project/backend/requirements.txt`)
- [x] Rewrote all 5 documentation files (README, QUICK_REFERENCE,
      FILE_BY_FILE_BREAKDOWN, HEALTHSAATHI_COMPLETE_ANALYSIS,
      PROJECT_STRUCTURE_VISUAL) to remove fabricated metrics and fix wrong
      counts. These live in a gitignored `documentation/` folder locally —
      not in the repo, so re-check they're current if working on them again.
- [x] Ablation study (`project/backend/ablation_study.py`) — per-role vs
      global IsolationForest comparison on identical 80% split, 6,902-row
      extended dataset. Original hypothesis ("per-role beats global") was
      tested and found to be a data-starvation artifact, NOT a real modeling
      advantage — this was reframed honestly rather than kept as a false claim.

## What's NOT done yet — pick up here

1. **Run `resource_efficiency_benchmark.py`** (at
   `project/backend/resource_efficiency_benchmark.py`) against the real
   dataset. This compares IsolationForest vs One-Class SVM vs a compact
   MLPRegressor-based autoencoder (8→4→8 bottleneck) on BOTH accuracy
   (precision/recall/F1/FPR) AND deployment cost (inference latency,
   training time, peak memory, model size on disk). This is the actual
   novelty contribution — see below.
   ```
   cd project/backend
   python resource_efficiency_benchmark.py --data path/to/09_audit_logs_synthetic.csv
   ```
   Report the REAL output. Do not estimate or pre-fill numbers.

2. **Write up the novelty section** for the report/paper once the benchmark
   has real numbers. Two-pronged claim:
   - Hash-chain tamper-detection latency benchmark (already have real numbers)
   - Resource-efficiency comparison showing what's actually deployable on
     low-resource clinic hardware, vs. the GNN/transformer direction the
     2024-2026 literature has moved toward without considering deployment cost

3. Nothing else is currently a known gap. If new gaps are found, verify them
   against actual code before reporting, the same way the earlier audit did.

## Novelty framing (why it matters, don't drift from this)

The original pitch was "per-role IsolationForest beats a global model" —
tested rigorously, found to be a data-starvation artifact of the original
5,000-row dataset (fixed by extending to 6,902 rows), NOT a genuine modeling
advantage. This was caught and the framing was changed to be honest.

**Current honest novelty claims (defend these, don't overstate them further):**
1. A labeled synthetic EHR audit-log dataset with documented anomaly archetypes
2. An empirical finding that insider-threat behavior shows a role-agnostic
   signature despite role-specific normal baselines
3. Hash-chain tamper-detection latency benchmarked at O(N) scaling, 100%
   detection across 27 trials
4. Read-level audit logging with behavioral trend escalation, closing a
   documented compliance gap
5. (in progress) Resource-efficiency benchmark — deployment-cost comparison
   the mainstream literature doesn't do, targeted at the real market gap
   (underserved small/mid Indian clinics with weak server hardware)

Do not claim the ML detection technique itself (IsolationForest+SHAP) is
novel. It isn't, as of the 2024-2026 literature. Market-fit-wise: the
HMS/queue-management side addresses a real gap; the security/anomaly side is
academically solid but isn't what the target customer (small clinic) actually
prioritizes day-to-day — keep that distinction honest in any writeup.

## Working style notes

- Vaani prefers direct, brief communication; switches between English/Hindi.
- Wants to be corrected when results contradict expectations, not reassured.
- Verify before documenting — confirm rate limits, counts, and any other
  claim against a live run or direct code inspection before writing it down.
- Run `flutter analyze` after Flutter changes and fix anything introduced
  (pre-existing deprecation warnings unrelated to your change are fine to
  leave — there are ~87 pre-existing ones as of last check, mostly
  `withOpacity()` deprecation notices, not something to fix unless asked).
- Sequence work by actual impact/risk, don't bundle unrelated changes into
  one large commit.
