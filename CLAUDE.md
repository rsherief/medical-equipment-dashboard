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

## Data standard (every data/*.xlsx)

Arabic headers, one device per row:
`الماركة | الموديل | الرقم المسلسل | الكود | تاريخ الانتاج | TRC | الحالة الفنية | وصف الحالة الفنية`

- `الحالة الفنية`: FF / PF / NF. `TRC`: 1–5 (criteria embedded in build.py).
- `وصف الحالة الفنية`: one fault per line inside the cell.
- Filename stem = category key in `config.json` (display names ar/en +
  expected life years). Duplicate codes are merged by build.py.

## Standing workflows (do these when asked, no re-planning needed)

1. **Fault report intake** — the user pastes a WhatsApp text, photo, or note
   about a device fault/repair. Find the device by code in the right
   `data/*.xlsx` (openpyxl), update الحالة الفنية / وصف الحالة الفنية / TRC
   accordingly, show the user the before→after row, then run `./update.sh`.
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
