# Discussion Summary: Reference Documents vs Logic

**Date:** 2026-07-13  
**Prepared for:** Fable 5 Implementation Handoff

---

## What We Found

Read all 6 reference documents + your classifications:
1. DOC-20260501-WA0011 (TRC criteria) ✓
2. BEAG Life Span Guidance Paper ✓
3. WHO Incubator Guidance ✓
4. Asset Management Classification ✓
5. INC.xlsx (sample data) ✓
6. Your decisions on questions 1–5 ✓

**Discovery:** The application logic is **close but incomplete**. The TRC thresholds are correct, but the *way they're applied* is oversimplified and misses critical business logic about device support & certification.

---

## The 3 Critical Issues

### Issue #1: TRC Suggestion Logic Is Backwards
**Current:** Downtime > 20% → downgrade to TRC 3  
**Correct:** Downtime < 20% AND cost < 20% → eligible for TRC 2 (not automatic)

**Example:** A 6-year-old device with 25% downtime currently scores TRC 2. It should be TRC 3 because it fails the downtime requirement.

**Fix:** Rewrite suggest_trc() to check ALL criteria (AND logic), not just thresholds (OR logic). See IMPLEMENTATION_PLAN.md Part 2.

---

### Issue #2: No Support/Spares Tracking
**Reference says:**
- TRC 3 = "Discontinued but support STILL AVAILABLE"
- TRC 4 = "Discontinued, NO support or parts"

**Current code:** Treats both the same; never checks manufacturer support status.

**Your decision:** Add `support_status` column to maintenance_log.xlsx:
- Supported/Active
- Limited Supported
- EOL (End of Life)
- Obsolete

**Impact:** Must populate this field manually in Excel going forward.

---

### Issue #3: Life Expectancy One-Size-Fits-All
**Current:** All devices assume 10 years  
**Reality:** Incubators 7–15 years (per WHO), other devices 2–25 years (per BEAG)

**Your decision:** Manually add to config.json per category, with model-specific overrides:
```json
"incubators": {
  "expected_life_years": 10,
  "incubator_models": {
    "Atom Rabee Incu i": 15,
    "Drager C2000": 15
  }
}
```

**Action needed:** Provide model → life years mapping for each device type.

---

## What Changes

### Schema Changes (You'll Need to Do)

| File | Column | Type | Values | Required? |
|------|--------|------|--------|-----------|
| **config.json** | `expected_life_years` | Int | Per category | Yes |
| **config.json** | `incubator_models` | Dict | Model → years | For incubators |
| **data/*.xlsx** | `certified` | Bool/Text | Yes/No | Yes (new) |
| **maintenance_log.xlsx** | `support_status` | Enum | Supported/Active, Limited, EOL, Obsolete | Yes (new) |

### Code Changes (Fable 5 Will Do)

| File | Function | Change | Impact |
|------|----------|--------|--------|
| build.py | `suggest_trc()` | Rewrite with AND logic | Medium (scores may shift) |
| build.py | `read_category()` | Extract `certified` + `support_status` | Low |
| build.py | New: `get_expected_life()` | Model-based life lookup | Low |

---

## Your Decisions (Confirmed)

| Question | Your Answer | Impact |
|----------|-------------|--------|
| Q1: Life expectancy mapping | Manually in config.json | Must edit config.json per category |
| Q2: Support tracking | New column in maintenance_log.xlsx | Must populate when logging maintenance |
| Q3: Incubator life | Look up from BEAG by model | Must provide model mappings |
| Q4: Certification | New field in data/*.xlsx | Must populate when adding devices |
| Q5: Testing | Validate against manual TRC first | Extra step before going live |

---

## What Happens Next (Fable 5)

### Step 1: Pre-Implementation Prep
Fable 5 will ask you for:
1. Incubator model → life years mapping (from BEAG paper)
   - Example: Atom Rabee Incu i → 15 years
2. Confirmation that maintenance_log.xlsx will have new column
3. Sample data showing how `certified` should be filled

### Step 2: Implementation
Fable 5 will:
1. Implement new schema (config.json, templates for Excel)
2. Rewrite suggest_trc() logic
3. Generate comparison report (old TRC vs new TRC for all devices)

### Step 3: Validation
You will:
1. Review comparison report
2. Spot-check 5–10 devices: are new TRCs correct?
3. Approve or iterate

### Step 4: Deploy
Fable 5 will:
1. Update CLAUDE.md with new requirements
2. Commit & push via update.sh
3. Run GitHub workflow

---

## Example: Before vs After

### Device A41 (Atom Rabee Incu i, 2015)

**Current (Wrong):**
```
Age: 11 years
Status: PF
Downtime: 15% per year
Cost: $200 cumulative
TRC Suggested: 3 (age ≤ 7 check: FAIL, so defaults to 3)
```

**After Fix (Correct):**
```
Age: 11 years (exceeds TRC 2 threshold of 7)
Status: PF (not FF, but downtime < 20%, so OK)
Downtime: 15% < 20% ✓
Cost: $200 / $1000 price = 20% ratio ✓ (borderline, needs cost ratio check)
Support: Limited Supported (from maintenance_log)
Certified: Yes

TRC Suggested: 3 (not TRC 2, because age > 7)
Reason: "Age exceeds 7-year TRC2 threshold; support status Limited"
```

---

## Open Questions Requiring Your Input

**Before Fable 5 starts, answer these:**

### Q1: Incubator Model Life Expectancy
Map each model in your fleet to expected years (from BEAG or WHO):
```
Atom Rabee Incu i       → ? years
Atom Air Incu i         → ? years
Drager C2000            → ? years
Drager C5000            → ? years
Other models → ?
```

### Q2: Maintenance Log Population
Going forward, who will fill `support_status` when logging maintenance?
- Option A: Defaults to "Supported/Active" for new entries (user overrides if needed)
- Option B: User manually selects every time (more accurate, more work)
- Option C: Import from external manufacturer database (if you have one)

### Q3: Existing Data Defaults
For devices already in Excel:
- Should `certified` default to "No" (conservative) or "Yes" (assume they were)?
- Should `support_status` default to "Supported/Active" or "Limited Supported"?

### Q4: Threshold Tolerance
Are you comfortable with TRC suggestions changing for existing devices?
- Example: A device currently TRC 3 might become TRC 4 if support_status is "EOL"
- Should we validate against your manual assessment before going live? (Yes per Q5)

### Q5: Timeline
Do you need this live by a specific date, or is thorough validation more important?

---

## Files Generated for Your Review

✅ **LOGIC_AUDIT.md** — Detailed audit of all gaps (8 findings)  
✅ **IMPLEMENTATION_PLAN.md** — Step-by-step implementation with code examples  
✅ **This document** — Discussion summary + decision points  
✅ **Reference docs** — All 6 originals still in `/docs/`

---

## Success Criteria

Before deploying to production:

- [ ] All new columns added to Excel templates
- [ ] config.json updated with model-specific life expectancy
- [ ] Fable 5 generates comparison report (old vs new TRC)
- [ ] You review ≥90% of TRC changes and validate
- [ ] CLAUDE.md updated with new data requirements
- [ ] Test run of `./update.sh` succeeds
- [ ] GitHub Pages site reflects new logic

---

## Next Steps

1. **Review this document** — Ensure you understand the 3 critical issues
2. **Answer the 5 open questions** — Provide model life years & defaults
3. **Approve the plan** — Sign off on schema + logic changes
4. **Fable 5 begins** → Implements → Generates comparison → You validate → Deploy

**Approval:** Confirm by replying:
> "Approved. Here are my answers to questions 1–5: ..."

---

**Prepared by:** Claude Haiku (this session)  
**For implementation by:** Fable 5  
**Date:** 2026-07-13
