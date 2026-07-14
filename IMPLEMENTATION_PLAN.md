# Implementation Plan: Logic Fixes & Schema Updates

**Date:** 2026-07-13  
**Model:** Fable 5  
**Status:** Ready for implementation (awaiting approval)

---

## Overview

Based on reference document audit + user decisions, this plan covers:

1. **Data schema changes** (config.json, data/*.xlsx, maintenance_log.xlsx)
2. **Rewrites to suggest_trc()** logic to match reference criteria exactly
3. **Validation approach** before pushing live
4. **Documentation updates** (CLAUDE.md, site/data.json)

---

## PART 1: Data Schema Changes

### 1.1 config.json Updates

**Current (incomplete):**
```json
{
  "default_expected_life_years": 10,
  "categories": {
    "incubators": {
      "name_en": "Incubators",
      "name_ar": "حاضنات",
      "expected_life_years": 10,
      "pm_interval_days": 90
    }
  }
}
```

**Required Changes:**

```json
{
  "default_expected_life_years": 10,
  "categories": {
    "incubators": {
      "name_en": "Incubators",
      "name_ar": "حاضنات",
      "expected_life_years": 10,
      "incubator_models": {
        "Atom Rabee Incu i": 15,
        "Atom Air Incu i": 12,
        "Drager C2000": 15,
        "Drager C5000": 15
      },
      "pm_interval_days": 90,
      "replacement_price": null
    }
  }
}
```

**Why:** Allow per-model life expectancy override (from BEAG table).

---

### 1.2 maintenance_log.xlsx Schema

**Current columns:**
```
التاريخ | الكود | نوع العمل | الوصف | أيام التوقف | التكلفة
```

**New column (insert after الكود):**
```
Column: "support_status" or "حالة الدعم الفني"
Type: Enum (dropdown)
Values: [
  "Supported/Active",
  "Limited Supported",
  "EOL",
  "Obsolete"
]
Default: "Supported/Active"
Required: Yes (or defaults to most recent known status)
```

**Rationale:** Tracks manufacturer support level; drives TRC 3 vs 4 distinction.

**Example rows:**
```
التاريخ        | الكود | حالة الدعم الفني | نوع العمل  | الوصف        | أيام التوقف | التكلفة
2026-07-01    | A1   | Supported/Active | إصلاح      | استبدال باب  | 1          | 150
2026-06-15    | D8   | EOL             | وقائية     | فحص دوري     | 0          | 50
```

---

### 1.3 data/*.xlsx (All Category Files)

**Current standard columns:**
```
الماركة | الموديل | الرقم المسلسل | الكود | تاريخ الانتاج | TRC | الحالة الفنية | وصف الحالة الفنية
```

**New column (insert after TRC):**
```
Column: "شهادة الجودة" or "Certified"
Type: Boolean / Text
Values: ["Yes" / "No"] or ["معتمد" / "غير معتمد"]
```

**Rationale:** TRC 1 requires "certified quality certificate" per DOC-20260501-WA0011.

**Example:**
```
الماركة | الموديل         | الرقم المسلسل | الكود | تاريخ الانتاج | شهادة الجودة | TRC | الحالة الفنية | وصف الحالة الفنية
Atom   | Air Incu i      | 200400240     | A53   | 2020         | Yes           | 2   | FF           | تعمل بكامل الكفاءة
Atom   | Rabee Incu i    | 2530063       | A41   | 2015         | Yes           | 4   | PF           | كسر فى أحد الابواب
```

---

## PART 2: Rewritten suggest_trc() Logic

### 2.1 Current Implementation (Broken)

```python
def suggest_trc(age, status, maint, price):
    """Data-driven TRC suggestion from the organization's own thresholds."""
    if not maint:
        return None
    downtime_pct = maint["downtime_pct"]
    cost_ratio = round(maint["cum_cost"] / price, 2) if price else None
    reasons = {"downtime_pct": downtime_pct, "cost_ratio": cost_ratio}

    # ISSUE 1: OR logic instead of AND
    if downtime_pct > 50 or (cost_ratio is not None and cost_ratio > 0.5):
        trc = 4
    elif downtime_pct > 20 or (cost_ratio is not None and cost_ratio > 0.2):
        trc = 3
    # ISSUE 2: TRC 1 ignores cost & support checks
    elif age is not None and age <= 3 and status == "FF":
        trc = 1
    # ISSUE 3: TRC 2 is age-only, ignores downtime & cost requirements
    elif age is not None and age <= 7:
        trc = 2
    else:
        trc = 3
    return {"trc": trc, **reasons}
```

### 2.2 Revised Implementation (Correct)

```python
def suggest_trc(age, status, maint, price, certified=False, support_status=None):
    """
    Data-driven TRC suggestion matching DOC-20260501-WA0011 criteria exactly.
    
    Args:
        age (int): Device age in years
        status (str): "FF" | "PF" | "NF"
        maint (dict): Maintenance analytics (downtime_pct, cum_cost, ...)
        price (float): Device replacement price
        certified (bool): Has certified quality certificate
        support_status (str): "Supported/Active" | "Limited Supported" | "EOL" | "Obsolete"
    
    Returns:
        dict: {"trc": 1-4, "reasons": {...}, "warnings": [...]}
    
    Logic follows TRC criteria hierarchy:
        TRC 1: All of [age ≤ 3, FF, certified, support=Supported/Active]
        TRC 2: All of [age ≤ 7, downtime <20%, cost <20%, support=Supported/Active]
        TRC 3: All of [downtime <50%, cost <50%, support∈{Supported/Active,Limited,EOL}]
        TRC 4: Any of [downtime ≥50%, cost ≥50%, support=Obsolete, unsupported]
    """
    if not maint:
        return None
    
    downtime_pct = maint["downtime_pct"]
    cost_ratio = round(maint["cum_cost"] / price, 2) if price else None
    warnings = []
    
    # TRC 4: Criteria for "do not rely on this equipment"
    if (downtime_pct > 50 
        or (cost_ratio is not None and cost_ratio > 0.5)
        or support_status == "Obsolete"):
        trc = 4
        warnings.append(f"Downtime {downtime_pct}% or cost {cost_ratio} exceeds limits, or support is Obsolete")
    
    # TRC 3: Criteria for "discontinued but still supported"
    elif (downtime_pct <= 50 
          and (cost_ratio is None or cost_ratio <= 0.5)
          and support_status in ["Supported/Active", "Limited Supported", "EOL"]):
        trc = 3
        if support_status == "EOL":
            warnings.append("Device is EOL; consider replacement within 2 years")
        if support_status == "Limited Supported":
            warnings.append("Device has limited support; parts may become unavailable")
    
    # TRC 2: Criteria for "recent, well-supported, reliable"
    # REQUIRES ALL: age ≤ 7, downtime <20%, cost <20%, support active, suitable status
    elif (age is not None and age <= 7
          and downtime_pct < 20
          and (cost_ratio is None or cost_ratio < 0.2)
          and support_status == "Supported/Active"
          and status in ["FF", "PF"]):  # PF acceptable if downtime low
        trc = 2
    
    # TRC 1: Criteria for "latest, most reliable, certified"
    # REQUIRES ALL: age ≤ 3, fully functional, certified, support active
    elif (age is not None and age <= 3
          and status == "FF"
          and certified
          and support_status == "Supported/Active"):
        trc = 1
    
    # Default: TRC 3 (grey area; flag for review)
    else:
        trc = 3
        reasons_for_3 = []
        if age and age > 7:
            reasons_for_3.append(f"Age {age}y exceeds TRC2 threshold")
        if downtime_pct >= 20:
            reasons_for_3.append(f"Downtime {downtime_pct}% at/near 20% threshold")
        if cost_ratio and cost_ratio >= 0.2:
            reasons_for_3.append(f"Cost ratio {cost_ratio} at/near 20% threshold")
        if support_status and support_status not in ["Supported/Active"]:
            reasons_for_3.append(f"Support status: {support_status}")
        warnings.append(f"Assigned TRC 3 by default; review: {'; '.join(reasons_for_3)}")
    
    return {
        "trc": trc,
        "downtime_pct": downtime_pct,
        "cost_ratio": cost_ratio,
        "age": age,
        "status": status,
        "certified": certified,
        "support_status": support_status,
        "warnings": warnings
    }
```

---

### 2.3 Integration with read_category()

**Current call (line 378 in build.py):**
```python
suggestion = suggest_trc(age, d["status"], d["maint"], price)
```

**Updated call:**
```python
# Extract new fields from Excel row
certified = rec.get("certified", "").lower() in ["yes", "true", "معتمد", "yes", "1"]
support_status = log_events.get(d["code"]).support_status if d["code"] in log_events else "Supported/Active"

suggestion = suggest_trc(
    age=age,
    status=d["status"],
    maint=d["maint"],
    price=price,
    certified=certified,
    support_status=support_status
)
```

**Note:** Support status will come from most recent entry in maintenance_log for that device.

---

## PART 3: Handling Incubator Model-Specific Life Expectancy

### 3.1 Add Incubator Model Lookup Function

```python
def get_expected_life(model_name, category_key, config):
    """
    Look up expected device life by model, fallback to category, then global.
    
    Priority:
    1. Exact model match in config.categories[category].incubator_models[model]
    2. Category-level default: config.categories[category].expected_life_years
    3. Global default: config.default_expected_life_years
    """
    if category_key in config.get("categories", {}):
        cat = config["categories"][category_key]
        
        # Try model-specific override
        if "incubator_models" in cat:
            for model_key, life_years in cat["incubator_models"].items():
                if model_key.lower() in model_name.lower():
                    return life_years
        
        # Try category default
        if "expected_life_years" in cat:
            return cat["expected_life_years"]
    
    # Fall back to global
    return config.get("default_expected_life_years", 10)
```

### 3.2 Use in read_category()

**Current (line 331):**
```python
expected_life = cat_cfg.get("expected_life_years", default_life)
```

**Updated:**
```python
expected_life = get_expected_life(rec.get("model"), key, config)
```

---

## PART 4: Validation Approach (Before Live Deployment)

### 4.1 Comparison Report

Before pushing changes, run both old and new suggest_trc() on all devices:

```python
# Compare old vs new
for device in all_devices:
    old_trc = old_suggest_trc(...)
    new_trc = new_suggest_trc(...)
    
    if old_trc["trc"] != new_trc["trc"]:
        print(f"⚠️  {device.code}: TRC {old_trc} → {new_trc}")
        print(f"   Reason: {new_trc['warnings']}")
```

### 4.2 User Review Checklist

- [ ] Run comparison on real fleet (site/data.json)
- [ ] Review all devices where TRC changed
- [ ] Check if new TRC matches your manual assessment
- [ ] Document any disagreements (may indicate bad maint data or criteria gap)
- [ ] Approve before adding to build.py

---

## PART 5: Documentation Updates

### 5.1 Update CLAUDE.md

Add new section:

```markdown
## TRC Logic (Automated Suggestion)

TRC 1–4 are auto-suggested based on:
- Device **age** vs expected life (per model in config.json)
- **Maintenance history**: downtime %, cumulative cost
- **Support status**: Supported/Active, Limited, EOL, Obsolete (from maintenance_log)
- **Certification**: Quality certificate (new field in data files)

Logic matches DOC-20260501-WA0011 criteria exactly. TRC 5 is never auto-suggested — 
it's a safety judgment reserved for the engineer.

### Data Requirements

**data/*.xlsx columns:**
- `certified`: "Yes" | "No" (new)

**maintenance_log.xlsx columns:**
- `support_status`: "Supported/Active" | "Limited Supported" | "EOL" | "Obsolete" (new)

### Configuration

**config.json:**
```json
{
  "categories": {
    "incubators": {
      "expected_life_years": 10,
      "incubator_models": {
        "Atom Rabee Incu i": 15,
        "Atom Air Incu i": 12,
        "Drager C2000": 15
      }
    }
  }
}
```

### Thresholds (from DOC-20260501-WA0011)

- TRC 2 → 3: Downtime ≥ 20% OR cost ≥ 20% of device price
- TRC 3 → 4: Downtime ≥ 50% OR cost ≥ 50% of device price
- Age: TRC 1 ≤ 3yr, TRC 2 ≤ 7yr (per manufacturer support status)
```

### 5.2 Add Asset Management Classification to site/data.json

Include in output:
```json
{
  "asset_classification": {
    "supported_active": "Manufacturer provides technical support, updates, training, spare parts",
    "limited_supported": "Equipment discontinued; some spare parts and support remain available",
    "eol": "Manufacturer ended routine support; parts difficult to obtain",
    "obsolete": "Equipment should be considered for replacement due to age, support, or regulatory concerns"
  }
}
```

---

## PART 6: Implementation Checklist

### Pre-Implementation Review
- [ ] User approves all schema changes (config.json, data*.xlsx, maintenance_log.xlsx)
- [ ] User provides incubator model → life years mappings for config.json
- [ ] User reviews revised suggest_trc() logic

### Phase 1: Data Schema (Non-Breaking)
- [ ] Add `expected_life_years` entries to config.json per category
- [ ] Add `incubator_models` mappings to config.json
- [ ] Add `support_status` column to maintenance_log.xlsx template
- [ ] Add `certified` column to data/*.xlsx template
- [ ] Update INC.xlsx sample with new columns

### Phase 2: Code Changes (Breaking)
- [ ] Add `get_expected_life()` function to build.py
- [ ] Rewrite `suggest_trc()` with new logic
- [ ] Update `read_category()` to pass new parameters
- [ ] Add new `support_status` field extraction from maintenance_log
- [ ] Add new `certified` field extraction from data files

### Phase 3: Validation
- [ ] Run `python3 build.py` to generate site/data.json (old format, but with new logic)
- [ ] Export comparison: old suggest_trc() vs new for all devices
- [ ] User reviews all TRC changes and validates
- [ ] Iterate on thresholds if needed

### Phase 4: Documentation & Release
- [ ] Update CLAUDE.md with new logic + data requirements
- [ ] Update config.json with example categories
- [ ] Commit with message: "Refactor TRC logic to match reference criteria exactly"
- [ ] Run `./update.sh` and push

---

## PART 7: Open Questions for User

Before implementing, confirm:

1. **config.json: Incubator models** — Provide model names & expected life years:
   ```json
   "incubator_models": {
     "Atom Rabee Incu i": ?,
     "Atom Air Incu i": ?,
     "Drager C2000": ?,
     "Drager C5000": ?
   }
   ```

2. **Maintenance log population** — Who will populate `support_status` going forward?
   - Will it default to "Supported/Active" for new entries?
   - Will user review & override per device in Excel?

3. **Backward compatibility** — For existing devices without `certified` or `support_status`:
   - Should `certified` default to "No" (conservative)?
   - Should `support_status` default to "Supported/Active" (most devices still active)?

4. **Threshold tolerance** — Any devices where new TRC is significantly different from old?
   - Should we adjust thresholds before live deployment?

---

## Risks & Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Schema conflicts if devices already have old `certified` field | Low | Check before adding column |
| User data incomplete (missing `support_status`) | Medium | Default to conservative value; flag in warnings |
| New logic breaks existing workflows | Medium | Validate against manual TRC first; iterate |
| Performance regression on large fleet | Low | suggest_trc() is O(1); no scaling issue |

---

## Success Criteria

✅ All devices' suggested TRC match reference criteria logic  
✅ User validates ≥90% of new suggestions vs manual assessments  
✅ No devices lose support/parts info during migration  
✅ CLAUDE.md clearly documents new fields & logic  
✅ site/data.json includes Asset Management Classification reference  

---

**Status:** Ready for Fable 5 implementation upon user approval.
