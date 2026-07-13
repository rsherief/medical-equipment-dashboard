# Medical Equipment Maintenance Dashboard | لوحة صيانة الأجهزة الطبية

Mobile-first, bilingual (Arabic/English) dashboard for medical equipment
maintenance and replacement planning. The Excel files in `data/` are the
source of truth; the site is a read-only view generated from them.

**Live site:** see the GitHub Pages URL in the repository settings.

## How it works

```
data/*.xlsx  →  build.py  →  site/data.json  →  static site (GitHub Pages)
```

- Each `.xlsx` in `data/` is one equipment category (e.g. `incubators.xlsx`).
- `build.py` parses the sheets, applies the organization's **TRC 1–5
  classification**, computes an explainable replacement-priority score
  (TRC + technical status + age vs. expected life), and extracts
  **spare-part needs** from the Arabic fault descriptions.
- The site shows: fleet dashboard, searchable device list, replacement
  plan (ranked), and an aggregated spare-parts list.

## Updating the dashboard | تحديث اللوحة

1. Edit or replace the Excel file(s) in `data/` — keep the standard columns:

   | الماركة | الموديل | الرقم المسلسل | الكود | تاريخ الانتاج | TRC | الحالة الفنية | وصف الحالة الفنية |
   |---------|---------|---------------|-------|----------------|-----|----------------|--------------------|

   - `الحالة الفنية`: `FF` (fully functional), `PF` (partial), `NF` (not functional)
   - `TRC`: 1–5 per the organization's classification guide
   - `وصف الحالة الفنية`: one fault per line (multi-line cells supported)

2. Run:

   ```bash
   ./update.sh
   ```

   This rebuilds `site/data.json`, commits, and pushes — GitHub Pages
   redeploys automatically in about a minute.

## Adding a new equipment category | إضافة فئة أجهزة جديدة

1. Drop a new Excel file in `data/` (same columns), e.g. `ventilators.xlsx`.
2. Add an entry in `config.json` with the display names and expected life
   span in years (see the BEAG life-span guidance paper in `docs/`):

   ```json
   "ventilators": {
     "name_en": "Ventilators",
     "name_ar": "أجهزة التنفس الصناعي",
     "expected_life_years": 10
   }
   ```

3. Run `./update.sh`. A category selector appears automatically in the app.

## Maintenance log & auto-TRC | سجل الصيانة

`data/maintenance_log.xlsx` (sheet **Log**) records every repair and
preventive-maintenance visit — one row per event:

| التاريخ | الكود | نوع العمل | الوصف | أيام التوقف | التكلفة |
|---------|-------|-----------|-------|--------------|---------|
| 2026-07-13 | A41 | إصلاح / وقائية | ... | 3 | 1500 |

From this log the dashboard computes downtime %, cumulative cost,
MTBF/MTTR, PM due dates (interval per category in `config.json`,
default 90 days), and a **data-suggested TRC** using the organization's
own thresholds. Set `replacement_price` in `config.json` to enable the
cumulative-cost criterion. TRC 5 is never auto-suggested — the safety
judgment stays with the engineer.

## In-app buttons

- **تقرير PDF** — generates a printable management report in the browser
  (use the phone's Print → Save as PDF).
- **تحديث الموقع** — opens the GitHub Actions page; tap "Run workflow" to
  rebuild the site instantly. The site also rebuilds automatically on every
  push and every Sunday 06:00 UTC.

## Local preview

```bash
python3 build.py
python3 -m http.server 8642 --directory site
# open http://localhost:8642
```

## Requirements

- Python 3 with `openpyxl` (`pip install openpyxl`)
- `git` + `gh` (GitHub CLI) for publishing
