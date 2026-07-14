# Logic Audit: Reference Documents vs Implementation

**Date:** 2026-07-13  
**Status:** Review Phase (before implementation)  
**Model:** Fable 5 (for implementation phase)

---

## Executive Summary

Audit of 5 reference documents against current hardcoded logic in `build.py`. Found **7 major gaps** and **2 documentation issues**. TRC classification criteria are substantially correct but simplified in automation logic; life expectancy assumptions lack per-category granularity.

---

## Reference Documents Reviewed

| Document | Content | Use in Code |
|----------|---------|-------------|
| `DOC-20260501-WA0011..docx` + `2..docx` | TRC criteria (1-5) in Arabic | Hardcoded in `TRC_CRITERIA` (lines 72-149) |
| BEAG Life Span Guidance Paper (PDF) | Expected life years by device GMDN code | Not used; 10-year global default in `config.json` |
| WHO Incubator Guidance (WhatsApp image 5.42 AM) | Incubators: 7-10 years baseline; 15+ if well-maintained | Not referenced; contradicts 10-year default |
| **Asset Management Classification (WhatsApp image 2.55 PM)** | **Support status taxonomy: Supported/Active, Limited Support, EOL, Obsolete** | **NEW — Maps to TRC levels** |
| INC.xlsx | Sample data showing standard column layout | Structure OK; used for initial design only |

---

## Detailed Findings

### GAP 1: TRC Criteria Accuracy ⚠️ MINOR

**Document vs Code:**
```
Document (Arabic from DOC-20260501-WA0011):
  TRC 1: "أحدث إنتاج للشركة المصنعة ولم يمر على انتاجة أكثر من 3 سنوات"

Code (build.py line 79):
  "أحدث إنتاج للشركة المصنعة ولم يمر على إنتاجه أكثر من 3 سنوات"
```

**Issue:** Spelling variation in Arabic ("انتاجة" vs "إنتاجه"). Minor but should match source exactly.

**Impact:** None (both mean "its production"), but code should mirror source for compliance/audit trail.

---

### GAP 2: TRC 2 Criterion D Missing English Translation ⚠️ MINOR

**Document criterion:**
- Arabic: "والجهاز يستخدم بصورة أساسية ويعتمد عليه"
- English translation missing in code

**Code (line 93):**
```python
"Used as primary equipment and relied upon",  # Present but generic
```

**Issue:** English phrasing is present but criterion is listed as a sub-requirement. Document structure (A/B/C/D) not reflected; should clarify it's *all four* required.

**Impact:** Low — meaning is preserved, but structure clarity lost.

---

### GAP 3: Life Expectancy Hardcoded to 10 Years Globally ⚠️ CRITICAL

**Evidence:**
1. `config.json` default: `default_expected_life_years: 10`
2. BEAG PDF: Incubators listed as 10 or 15 years depending on type (GMDN code)
3. WHO image: "According to WHO the life expectancy of infant incubators is 7 - 10 years. Well maintained incubators can reach easily 15 years or more."

**Issue:** 
- Global 10-year default does not match device-specific guidance
- Incubators (your primary fleet) should be 7–10 years baseline, 15+ if maintained
- BEAG lists dozens of device types with life spans ranging **2–25 years**

**Current Code Impact:**
```python
# build.py line 369
age = (CURRENT_YEAR - d["year"]) if d["year"] else None

# score_device() line 306-307
if age is not None and expected_life:
    score += min(age / expected_life, 1.5) * 10
```

A 2010 incubator (16 years old) vs 2015 one (11 years old) both calculated wrong because they use 10-year baseline instead of the 7–15 range implied by WHO guidance.

**Impact:** HIGH — Replacement priority scores systematically biased for devices past "expected" life.

---

### GAP 4: suggest_trc() Oversimplifies Criterion Logic ⚠️ MAJOR

**Document criteria structure (TRC 2 example):**
```
TRC 2 requires ALL of:
  A. Relatively recent (< 7 years)
  B. Technical support from manufacturer & agent
  C. Downtime < 20% AND cost < 20% of equivalent device  ← Both required
  D. Used as primary equipment
```

**Current Code (lines 275–298):**
```python
def suggest_trc(age, status, maint, price):
    if downtime_pct > 50 or cost_ratio > 0.5:
        trc = 4  # ✓ Correct
    elif downtime_pct > 20 or cost_ratio > 0.2:
        trc = 3  # ✓ Correct (downtime>20 OR cost>20)
    elif age is not None and age <= 3 and status == "FF":
        trc = 1  # ✗ WRONG — missing criteria checks
    elif age is not None and age <= 7:
        trc = 2  # ✗ WRONG — age alone insufficient
    else:
        trc = 3
```

**Issues:**
1. **TRC 1 suggestion:** Requires "FF" status + age ≤ 3 years only. Document requires:
   - Latest production (< 3 years) ✓
   - Works efficiently ✓ (FF implies this)
   - **Certified quality certificate** ✗ (never checked)

2. **TRC 2 suggestion:** Age ≤ 7 is checked, but:
   - No verification of manufacturer support (not in maint data)
   - Downtime & cost checks only if they *exceed* thresholds (backwards logic)
   - Should require downtime <20% AND cost <20%, not use as downgrade triggers

3. **Missing TRC 3 nuance:** Document says "production discontinued BUT support available" — code never checks if device is orphaned vs still supported.

**Impact:** MEDIUM-HIGH — Suggestions may under-rate devices with good maintenance history.

---

### GAP 5: Incomplete Maintenance Analytics for TRC Decisions ⚠️ MEDIUM

**Document requires checking:**
- "دعم فني من الشركة المصنعة والوكيل المعتمد" (Technical support from manufacturer & authorized agent)
- "قطع غيار" (Spare parts availability)

**Code (build.py lines 234–272):**
```python
def maintenance_analytics(evs, pm_interval_days):
    # Computes: downtime_12m, cost_12m, cum_cost, mtbf, mttr, PM schedule
    # ✗ Never checks: manufacturer support status, spare parts availability
```

**Issue:** Logic to suggest TRC 3 (production discontinued, support still available) vs TRC 4 (discontinued, no support) depends on external data (manufacturer EOL date, agent status) not captured in Excel or maintenance log.

**Impact:** MEDIUM — TRC 3 vs 4 distinction will be inaccurate without support/spares data source.

---

### GAP 6: TRC 5 Never Auto-Suggested (Correct) ✓

**Document:** TRC 5 = "معطل" (Out of service). Criteria: Unsafe, no repair feasibility, no parts.

**Code (line 279):**
```python
# Never suggests TRC 5 — the unsafe / no-spare-parts judgment stays with the engineer.
```

**Status:** ✓ CORRECT — Safety decisions rightly remain manual.

---

### GAP 7: Status FF/PF/NF Thresholds Not in Document ⚠️ INFORMATION GAP

**Code defines (line 37):**
```python
STATUS_RANK = {"NF": 3, "PF": 2, "FF": 1}
```

**Document source:** TRC criteria reference "FF" / "PF" / "NF" but do not define them.

**Assumption in code:** 
- NF = Non-Functional (highest priority)
- PF = Partially Functional
- FF = Fully Functional (lowest priority)

**Issue:** These status definitions should be documented in a reference (likely in BEAG or WHO materials not yet found).

**Impact:** LOW — Interpretation is logical, but should be verified against official source.

---

### GAP 8: Spare Parts Extraction Logic Not Validated ⚠️ INFORMATION GAP

**Code (lines 169–186):**
```python
def extract_parts(fault_line):
    # Detects Arabic terms: "لوك شباك" (window lock), "المرطب" (humidifier), etc.
    # Patterns hardcoded; no reference document validates this list.
```

**Source:** Built from operational experience (visible in INC.xlsx fault descriptions).

**Issue:** No authoritative source to verify parts list is complete.

**Impact:** LOW — Functional but unmaintained (new part types require manual code updates).

---

## Summary Table: Gaps by Severity

| ID | Gap | Severity | Current Impact | Recommendation |
|----|----|----------|-----------------|-----------------|
| 1 | Arabic spelling in TRC 1 | Minor | None | Fix to match document |
| 2 | TRC 2 English translation incomplete | Minor | Low | Clarify criterion structure |
| 3 | Life expectancy hardcoded to 10yr globally | Critical | High | Implement per-device life spans from BEAG table |
| 4 | suggest_trc() oversimplifies criteria | Major | Medium-High | Refactor to match all criteria logically |
| 5 | No support/spares data collection | Medium | Medium | Add fields to maintenance_log for EOL/support status |
| 6 | TRC 5 never auto-suggested | Good ✓ | N/A | Maintain as-is (safety decision) |
| 7 | Status definitions not documented | Minor | Low | Add reference to FF/PF/NF definitions |
| 8 | Spare parts list not validated | Minor | Low | Consider making configurable |

---

## Before/After: Key Logic Changes Needed

### 1. Life Expectancy by Device Type
```python
# BEFORE: Global default
default_life = config.get("default_expected_life_years", 10)

# AFTER: GMDN-based lookup
def get_expected_life(gmdn_code, category_key, config):
    # Check BEAG table by GMDN code
    # Fall back to config category setting
    # Fall back to global default
```

### 2. TRC 2 Suggestion Logic
```python
# BEFORE: age <= 7 only
elif age is not None and age <= 7:
    trc = 2

# AFTER: All criteria must pass
elif (age is not None and age <= 7 
      and downtime_pct < 20 
      and (cost_ratio is None or cost_ratio < 0.2)):
    trc = 2
```

### 3. TRC 3 vs TRC 4 Distinction
```python
# BEFORE: Not distinguished
# AFTER: Check manufacturer_support and spares_available fields
if not manufacturer_support:
    trc = 4  # No support available
else:
    trc = 3  # Support available
```

---

## Questions for Discussion

1. **GMDN Mapping:** Should we extract GMDN codes from Excel or add them manually to config?
2. **Support/Spares Data:** Where should "manufacturer EOL date" and "agent support status" live? New columns in data files?
3. **Quality Certification:** For TRC 1, should we add a "certified" boolean field, or infer from "FF + < 3 years"?
4. **WHO Incubator Guidance:** Should we hard-code incubator expected life as 7–15 years, or load from BEAG table?
5. **Backwards Compatibility:** Will changing suggest_trc() thresholds significantly alter existing device scores?

---

## Implementation Plan (Fable 5)

- [ ] **Phase 1:** Extract GMDN/life-span mapping from BEAG PDF → `beag_reference.json`
- [ ] **Phase 2:** Update `suggest_trc()` to check all criteria (not just thresholds)
- [ ] **Phase 3:** Add manufacturer support / spare-parts tracking to maintenance log schema
- [ ] **Phase 4:** Test suggest_trc() on real fleet data; validate against manual engineer assessment
- [ ] **Phase 5:** Update CLAUDE.md and config.json with new requirements

---

## NEW: Asset Management Classification ↔ TRC Mapping

**Document:** WhatsApp Image 2.55.10 PM (2026-07-13)

This provides **critical definitions** for support status — resolves GAP 5 (missing support/spares checks):

### Support Status Definitions & TRC Alignment

| Support Status | Definition | TRC Level(s) | Key Attribute |
|---|---|---|---|
| **Supported / Active** | Manufacturer provides tech support, updates, training, spare parts | TRC 1–2 | "Recent production, manufacturer support available" |
| **Limited Support (Legacy)** | Discontinued but spare parts & support still available | TRC 3 | "Production discontinued but support available" |
| **EOL (End of Life)** | Routine support ended; parts difficult to obtain | TRC 3–4 | Depends on spares availability |
| **Obsolete** | Should replace: age, support gaps, tech advancement, regulatory risk | TRC 4–5 | "No support, no parts, unsafe" |

---

### Translation to Database Schema

**New column in `maintenance_log.xlsx`:**
```
Column: "support_status"
Values: [ "Supported/Active" | "Limited Supported" | "EOL" | "Obsolete" ]
```

This field will inform suggest_trc() logic:
```python
# TRC 3 vs 4 decision now clear
if manufacturer_support in ["Supported/Active", "Limited Supported"]:
    trc = 3  # "Production discontinued but support available"
elif manufacturer_support in ["EOL", "Obsolete"]:
    trc = 4  # "No support or limited support"
```

---

## User Decisions (2026-07-13)

**Q1: Life Expectancy Mapping**  
Decision: (B) Manually add `expected_life` to each category in `config.json`  
Rationale: User manages categories directly; simpler than GMDN lookup  
*Impact:* Must update `config.json` entries for all device categories with years

**Q2: Support/Spares Tracking**  
Decision: Add new column to `maintenance_log.xlsx`: support_status (enum)  
Options: "Supported/Active" | "Limited Supported" | "EOL" | "Obsolete"  
*Impact:* Schema change; users must maintain this field going forward

**Q3: Incubator Life Expectancy**  
Decision: Look it up from BEAG (different based on model type)  
*Impact:* Extract incubator models from BEAG table; override global default per model in config.json

**Q4: Certified Quality Requirement (TRC 1)**  
Decision: Add field in Excel to mark certified vs uncertified  
New column in data files: "شهادة الجودة" or "certified" (boolean)  
*Impact:* Schema change; users must populate when adding devices

**Q5: Testing Strategy**  
Decision: Validate against manual TRC assessments first  
*Impact:* Before pushing live, compare old vs new suggest_trc() output on real fleet

---

## Revised Implementation Scope (Fable 5)

With user decisions + Asset Management Classification, scope is now:

**Phase 1: Data Schema Updates**
- [ ] Add `expected_life_years` per category in `config.json`
- [ ] Add `support_status` column to `maintenance_log.xlsx` (enum: Supported/Active, Limited Supported, EOL, Obsolete)
- [ ] Add `certified` boolean column to all data/*.xlsx files
- [ ] Add incubator model → life expectancy lookup (from BEAG)

**Phase 2: Logic Refactoring (suggest_trc)**
- [ ] Rewrite to check ALL criteria (not OR thresholds)
- [ ] Use support_status to distinguish TRC 3 vs 4
- [ ] Check certified flag for TRC 1 eligibility
- [ ] Add age-based adjustments using per-category expected_life

**Phase 3: Validation**
- [ ] Run old + new suggest_trc() on real fleet data
- [ ] Compare output against user's manual TRC assessments
- [ ] Document differences; iterate until alignment

**Phase 4: Documentation**
- [ ] Update CLAUDE.md with new TRC logic
- [ ] Document new data fields (certified, support_status)
- [ ] Add Asset Management Classification to site/data.json (reference info)

---

## Document Versions & Changes

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-13 | Initial audit; 8 findings identified |
| 1.1 | 2026-07-13 | Added Asset Management Classification; incorporated user decisions; revised implementation scope |
| 1.2 | 2026-07-13 | **Implemented.** See resolution status below. |

---

## Resolution Status (v1.2)

| ID | Gap | Resolution |
|----|-----|-----------|
| 1 | Arabic spelling in TRC 1 | **Resolved by normalization** — source doc contains typos (انتاجة); code keeps normalized spelling (إنتاجه) for the public dashboard. Meaning identical. |
| 2 | TRC 2 criterion structure | **Resolved** — suggest_trc() now enforces all TRC 2 criteria jointly (AND-logic). |
| 3 | Life expectancy global 10y | **Resolved** — `model_life_years` in config.json (BEAG: infant incubators = 15y, all 5 fleet models). Category fallback 10y for unknown models. `past_expected_life` stat now per-device. |
| 4 | suggest_trc() OR-logic | **Resolved** — rewritten as AND-logic per DOC-20260501-WA0011; works without maintenance history (flagged `unverified`); NF ⇒ TRC 4 + nf_review warning. |
| 5 | No support/spares tracking | **Resolved** — `حالة الدعم الفني` column in maintenance_log.xlsx (dropdown: Supported/Active, Limited Supported, EOL, Obsolete); config `model_support_status` fallback (Drager C2000 = Limited per prior research); drives TRC 3 vs 4. |
| 6 | TRC 5 never auto-suggested | **Kept** as designed. |
| 7 | FF/PF/NF definitions | Open — interpretation documented in code; no official source found yet. |
| 8 | Spare-parts list unvalidated | Open — unchanged; still hardcoded patterns in build.py. |

**Validation:** see TRC_VALIDATION_REPORT.md (79 devices: 29 agree, 50 differ — 34 of them are manual TRC 4 → suggested TRC 3, pending downtime/support data; 5 are TRC 5 → 4 by design). **Not yet pushed** — awaiting user validation per their Q5 decision.
