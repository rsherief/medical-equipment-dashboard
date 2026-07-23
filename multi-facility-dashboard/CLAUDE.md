# Multi-Facility Dashboard

A standalone copy of the medical equipment maintenance dashboard (see the
repo-root `CLAUDE.md` for the original single-fleet version) that tracks
**multiple independent fleets** — the user's own equipment plus other
hospitals'/departments' equipment — switchable from a listbox in the site.
This folder is fully self-contained: its own `data/`, `site/`, `build.py`,
`config.json`, `update.sh`. It does not read or write anything under the
repo-root `data/`/`site/`/`build.py` — those stay exactly as they were.

## Pipeline

```
data/*.xlsx  →  python3 build.py  →  site/data.json  →  (not yet deployed)
```

Run from inside this folder: `cd multi-facility-dashboard && ./update.sh`.

- Live site: https://rsherief.github.io/medical-equipment-dashboard/multi-facility-dashboard/
- The repo-root `.github/workflows/pages.yml` builds **both** apps on every
  push to `main` (root `build.py`, then this folder's `build.py`), stages
  the original site at `/` and this one at `/multi-facility-dashboard/`,
  and deploys both together as one GitHub Pages artifact. `update.sh` here
  just builds + commits + pushes like the original app's script — the
  workflow does the actual combined deploy.

## Data standard (every data/*.xlsx and data/facilities/<key>/*.xlsx)

Same Arabic-header standard as the original app, one device per row (matched
by header name, not position):
`الماركة | الموديل | الرقم المسلسل | الكود | تاريخ الانتاج | TRC | شهادة الجودة | الحالة الفنية | وصف الحالة الفنية`

- `الحالة الفنية`: FF / PF / NF. `TRC`: 1–5 (criteria embedded in build.py).
- `شهادة الجودة`: Yes/No dropdown — required for a TRC 1 suggestion.
- `وصف الحالة الفنية`: one fault per line inside the cell.
- Filename stem = category key in `config.json` (display names ar/en,
  expected life years, per-model overrides). Duplicate codes are merged.

## Facilities (multi-hospital/department)

- The user's own equipment lives at `data/*.xlsx` — the **`main`** facility.
- Every other hospital/department gets its own folder:
  `data/facilities/<key>/`, containing category `.xlsx` files in the same
  standard format, and optionally its own `maintenance_log.xlsx`. `<key>` is
  a short slug (e.g. `alnour_nicu`).
- Each facility needs a matching entry under `config.json → facilities`
  (`name_en`/`name_ar`, optionally `hospital_en/ar`, `department_en/ar`), or
  `build.py` skips it with a warning.
- `build.py` builds each facility independently into
  `site/data.json → facilities.<key>.categories.<category>`.
- No client-side upload — GitHub Pages is static. Importing a new facility
  is Claude-mediated: the user hands over the Excel file, Claude saves it
  under `data/facilities/<key>/`, registers it in `config.json`, reruns
  `build.py`.
- Each hospital/department is an **independent fleet** — its own devices,
  categories, and stats, isolated from every other facility.

## Maintenance log (data/maintenance_log.xlsx and data/facilities/<key>/maintenance_log.xlsx)

Sheet "Log", one row per event (matched by header name):
`التاريخ | الكود | حالة الدعم الفني | نوع العمل | الوصف | أيام التوقف | التكلفة`
- `نوع العمل`: `إصلاح` (repair) or `وقائية` (preventive maintenance).
- `حالة الدعم الفني`: Supported/Active, Limited Supported, EOL, Obsolete.
  Latest non-empty value per device wins; config `model_support_status` is
  the fallback; unknown is assumed Supported/Active with a warning.
- build.py computes: downtime %, cumulative cost, MTBF/MTTR, PM due dates,
  and a **data-suggested TRC** (DOC-20260501-WA0011 criteria, AND-logic) —
  same rules as the original app (see repo-root `CLAUDE.md` for the full
  TRC 1–4 breakdown; TRC 5 is never auto-suggested).

## Standing workflows

1. **Fault report intake** — same as the original app: find the device by
   code in the right facility's `data/*.xlsx`, update
   الحالة الفنية / وصف الحالة الفنية / TRC, append a row to that facility's
   `maintenance_log.xlsx`, show before→after, run `./update.sh`.
2. **Add a hospital/department fleet** — user hands over an Excel file for
   another facility. Pick a facility key + display names (ask if not given),
   create `data/facilities/<key>/`, save the file(s) there, register it
   under `config.json → facilities`, run `./update.sh`.
3. **"Update the dashboard"** — run `./update.sh` from this folder; report
   the build summary.
