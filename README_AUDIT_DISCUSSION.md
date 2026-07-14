# Logic Audit & Implementation Discussion — Complete Summary

**Date:** 2026-07-13  
**Status:** Ready for your review & decision before Fable 5 implementation

---

## What You Asked

> "Have you considered the five files I uploaded to the docs folder, or did you use some of them?"

**Answer:** I read all 6 reference documents + your classifications carefully. Found **gaps between the reference guidance and current code logic**. Documented everything before implementing, as you requested.

---

## What I Did

### 1. Read All Reference Documents
✅ DOC-20260501-WA0011 (Arabic TRC criteria)  
✅ BEAG Life Span Guidance Paper (device life expectancy by type)  
✅ WHO Incubator Guidance (7–15 year incubator life)  
✅ **Your Asset Management Classification** (support status definitions)  
✅ INC.xlsx (sample data structure)  

### 2. Identified 8 Gaps
- 3 **Critical** (life expectancy, suggest_trc logic, support tracking)
- 2 **Major** (certification check, TRC 3 vs 4 distinction)
- 3 **Minor** (Arabic spelling, English translation, status definitions)

See: **LOGIC_AUDIT.md**

### 3. Got Your Decisions on 5 Key Questions
✅ Q1: Manually add expected_life to config.json (not GMDN lookup)  
✅ Q2: Add support_status column to maintenance_log.xlsx  
✅ Q3: Look up incubator life from BEAG by model  
✅ Q4: Add certified field to data/*.xlsx files  
✅ Q5: Validate against manual TRC assessments before going live  

### 4. Created Implementation Plan
Detailed code examples, data schema changes, validation approach, and testing strategy.

See: **IMPLEMENTATION_PLAN.md**

### 5. Mapped Everything Together
Created visual reference showing how Asset Management Classification connects to TRC levels.

See: **REFERENCE_MAPPING.md**

---

## Documents Created for Your Review

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **LOGIC_AUDIT.md** | Detailed analysis of all 8 gaps; maps reference docs to current code | 10 min |
| **DISCUSSION_SUMMARY.md** | Executive summary of 3 critical issues + 5 open questions | 8 min |
| **IMPLEMENTATION_PLAN.md** | Step-by-step implementation with code examples + schema changes | 15 min |
| **REFERENCE_MAPPING.md** | Quick lookup: Asset Status ↔ TRC ↔ Data Fields | 5 min |
| **This file** | Navigation guide | 3 min |

**Total read time:** ~40 minutes  
**Recommended:** Start with DISCUSSION_SUMMARY.md, then REFERENCE_MAPPING.md, then deep-dive into IMPLEMENTATION_PLAN.md

---

## The 3 Critical Issues (TL;DR)

### Issue #1: TRC Logic Is Backwards
**Current code:** `if downtime > 20% then downgrade to TRC 3`  
**Reference says:** Device must have downtime < 20% AND cost < 20% to qualify for TRC 2 (not automatic)

### Issue #2: Missing Support/Spares Tracking
**Reference says:** TRC 3 = "discontinued but support still available" vs TRC 4 = "no support"  
**Current code:** Doesn't distinguish between them

### Issue #3: Life Expectancy Hardcoded to 10 Years
**Reference says:** Incubators 7–15 years (per WHO), devices range 2–25 years (per BEAG)  
**Current code:** All devices use 10-year baseline

**Fix for all 3:** New data schema + rewritten suggest_trc() function

---

## What Needs to Change

### Excel Files (You manage)
- Add `certified` column to data/*.xlsx (Yes/No flag)
- Add `support_status` column to maintenance_log.xlsx (Supported/Active, Limited, EOL, Obsolete)

### config.json (You update with values I'll provide template for)
- Add `expected_life_years` per category
- Add `incubator_models` mapping (model name → life years)

### build.py (Fable 5 will implement)
- Rewrite suggest_trc() function (90 lines → 150 lines, more logic)
- Add get_expected_life() function (model-based lookup)
- Extract new fields from Excel (certified, support_status)

---

## Your Next Step: Provide 5 Answers

**Before Fable 5 starts, I need:**

### 1. Incubator Model Life Expectancy
From BEAG paper or WHO guidance, map each model you use:
```
Atom Rabee Incu i     → ___ years
Atom Air Incu i       → ___ years
Drager C2000          → ___ years
Drager C5000          → ___ years
[Other models]        → ___ years
```

### 2. Maintenance Log Defaults
When logging maintenance, should `support_status`:
- A) Default to "Supported/Active" (user overrides if needed)
- B) User manually selects every time
- C) Import from external database

### 3. Existing Data Defaults
For devices already in Excel:
- Should `certified` default to "Yes" or "No"?
- Should `support_status` default to "Supported/Active" or "Limited Supported"?

### 4. Threshold Tolerance
Is it OK if device TRC scores change for existing devices?  
(Example: Device currently TRC 3 might become TRC 4 if support_status is "EOL")

### 5. Timeline
When do you need this live? Thorough validation is important — any deadline?

---

## What Happens After You Approve

### Phase 1: Fable 5 Prepares Implementation (1 hour)
- Confirms your answers to questions 1–5
- Creates config.json template with your model mappings
- Generates Excel templates with new columns

### Phase 2: Fable 5 Implements (2–3 hours)
- Updates config.json
- Rewrites suggest_trc() function
- Runs `python3 build.py` to generate new site/data.json

### Phase 3: Comparison & Validation (1–2 hours, you do this)
- Fable 5 generates report: "Device X: TRC {old} → {new} because {reason}"
- You review ≥90% of devices that changed
- Spot-check manual calculations (5–10 devices)
- Approve or request adjustments

### Phase 4: Deploy (30 min)
- Update CLAUDE.md
- Commit & push via `./update.sh`
- Test on GitHub Pages

**Total time to live:** ~6–8 hours (mostly waiting on your review)

---

## Files You Can Read Now

Start with these in order:

1. **DISCUSSION_SUMMARY.md** ← Start here (10 min overview)
2. **REFERENCE_MAPPING.md** ← Quick visual reference (5 min)
3. **IMPLEMENTATION_PLAN.md** ← Deep dive if you want details (15 min)
4. **LOGIC_AUDIT.md** ← Full technical audit (10 min)

---

## Key Takeaways

✅ **References are well-structured** — TRC criteria, support definitions, life expectancy tables all present  
✅ **Current code captures most thresholds correctly** — But applies them wrong (OR instead of AND)  
✅ **Your classifications are spot-on** — Asset Management Classification maps perfectly to TRC levels  
✅ **No breaking changes needed** — Just data schema additions + logic fixes  
✅ **User in control** — You decide model life years, support tracking, validation depth  

---

## Ready to Proceed?

1. ✅ Read DISCUSSION_SUMMARY.md (you're here)
2. ✅ Read REFERENCE_MAPPING.md (visual reference)
3. ⏳ Provide answers to 5 open questions (above)
4. ✅ Approve or request adjustments
5. → Fable 5 implements

**Reply when ready with:**
> "Approved. Here are my answers:  
> 1. Model life expectancy: [your data]  
> 2. Maintenance log defaults: [choice A/B/C]  
> 3. Existing data defaults: [your choices]  
> 4. Threshold tolerance: [yes/no/conditional]  
> 5. Timeline: [your deadline]"

---

## Questions Before You Proceed?

Feel free to ask about:
- Any of the 8 gaps identified
- How the new suggest_trc() logic works
- Data schema impact (existing files, templates)
- Timeline & effort
- Risk mitigation
- Anything in IMPLEMENTATION_PLAN.md

**I'm here to discuss before Fable 5 implements.** Once you approve, the implementation becomes Fable 5's responsibility (and speed will increase significantly).

---

**Status:** ✅ All analysis complete. Awaiting your approval to proceed to Fable 5.
