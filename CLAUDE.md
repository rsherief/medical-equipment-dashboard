# Medical Equipment Maintenance Dashboard

The user is a biomedical engineer. The Excel files in `data/` are the single
source of truth for the equipment fleet; the site in `site/` is a read-only
dashboard generated from them. **The user's goal is to stop editing Excel
manually — Claude does the data entry, analysis, and publishing for them.**

## Pipeline

```
data/*.xlsx  →  python3 build.py  →  site/data.json  →  GitHub Pages
```

- Repo: https://github.com/rsherief/medical-equipment-dashboard (public)
- Live site: https://rsherief.github.io/medical-equipment-dashboard/
- Publish: `./update.sh` (build + commit + push). Pushes may require the
  user's approval in auto mode — if a push is blocked, hand the exact
  command to the user instead of retrying.
- CI also runs build.py (GitHub Actions: on push, weekly cron, and manual
  dispatch — the in-app "تحديث الموقع" button links to the workflow page).

## Data standard (every data/*.xlsx)

Arabic headers, one device per row (matched by header name, not position):
`الماركة | الموديل | الرقم المسلسل | الكود | تاريخ الانتاج | TRC | شهادة الجودة | الحالة الفنية | وصف الحالة الفنية`

- `الحالة الفنية`: FF / PF / NF. `TRC`: 1–5 (criteria embedded in build.py).
- `شهادة الجودة`: Yes/No dropdown — a certified quality certificate is a hard
  requirement for a TRC 1 suggestion. Blank = not certified (conservative).
- `وصف الحالة الفنية`: one fault per line inside the cell.
- Filename stem = category key in `config.json` (display names ar/en,
  expected life years, optional per-model `model_life_years` overrides from
  the BEAG table, and `model_support_status` defaults). Duplicate codes are
  merged by build.py.

## Maintenance log (data/maintenance_log.xlsx — NOT a category file)

Sheet "Log", one row per event (matched by header name):
`التاريخ | الكود | حالة الدعم الفني | نوع العمل | الوصف | أيام التوقف | التكلفة`
- `نوع العمل`: `إصلاح` (repair) or `وقائية` (preventive maintenance).
- `حالة الدعم الفني`: dropdown — Supported/Active, Limited Supported, EOL,
  Obsolete (Asset Management Classification, docs/WhatsApp 2.55 PM image).
  Latest non-empty value per device wins; config `model_support_status` is
  the fallback; unknown is assumed Supported/Active with a warning.
- build.py computes from it: downtime %, cumulative cost, MTBF/MTTR,
  PM due dates (interval per category in config.json), and a
  **data-suggested TRC** applying DOC-20260501-WA0011 criteria as AND-logic:
  - TRC 1: age ≤ 3 AND FF AND certified AND support Supported/Active
  - TRC 2: age ≤ 7 AND downtime < 20% AND cost < 20% of `replacement_price`
    AND support Supported/Active
  - TRC 3: still supported (incl. Limited/EOL), downtime ≤ 50%, cost ≤ 50%
  - TRC 4: downtime > 50% OR cost > 50% OR support Obsolete OR device NF
  - TRC 5 is **never** auto-suggested — safety judgment stays with the
    engineer (NF devices get TRC 4 plus a review warning instead).
  Suggestions work without a log too (age/support/certificate only) but are
  flagged unverified. Warnings are language-neutral codes translated in
  site/app.js (warn_* keys).

## Standing workflows (do these when asked, no re-planning needed)

1. **Fault report intake** — the user pastes a WhatsApp text, photo, or note
   about a device fault/repair. Find the device by code in the right
   `data/*.xlsx` (openpyxl), update الحالة الفنية / وصف الحالة الفنية / TRC
   accordingly, **and append a row to data/maintenance_log.xlsx** (repair
   events with downtime days and cost when known; PM visits as وقائية).
   Show the user the before→after rows, then run `./update.sh`.
   New device → append a row following the standard.
2. **"Update the dashboard"** — run `./update.sh`; report the build summary.
3. **Fleet questions** — answer from `site/data.json` (regenerate first if
   Excel changed). Scores and spare-part extraction logic live in build.py.
4. **Reports** — generate Arabic-first documents (docx/pdf/xlsx skills) from
   the data: fleet status, replacement budget, spare-parts procurement list.
5. **Market/support research** — when replacement or TRC downgrades are
   discussed, web-search the model's production/support status (e.g. Dräger
   Isolette C2000 is discontinued; third-party parts still available) and
   cite sources.

Always keep `docs/` untouched — those are the user's original reference
documents (TRC criteria, BEAG life-span paper, WHO incubator guidance).
