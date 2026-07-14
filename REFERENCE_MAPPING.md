# Quick Reference: Asset Status ↔ TRC Mapping

This document shows how the Asset Management Classification (WhatsApp 2.55 PM) maps to TRC levels (DOC-20260501-WA0011).

---

## TRC Classification (DOC-20260501-WA0011)

| TRC | Verdict (Arabic) | Verdict (English) | Key Criteria | Auto-Suggested |
|-----|------------------|-------------------|-----|---|
| **1** | يعمل ويعتمد عليه | Working & Dependable | Latest production (<3yr), certified, supported | Only if: age≤3 + FF + certified + supported |
| **2** | يعمل ويعتمد عليه | Working & Dependable | Recent (<7yr), supported, downtime<20%, cost<20%, primary use | Only if: age≤7 + downtime<20% + cost<20% + supported |
| **3** | يعمل ويعتمد عليه | Working & Dependable | Discontinued but supported, downtime<50%, cost<50% | If: support∈{Limited,EOL} + downtime<50% + cost<50% |
| **4** | يعمل ولكن لا يعتمد عليه | Working but NOT Dependable | Discontinued, no support, frequent failures, high cost | If: downtime>50% OR cost>50% OR support=Obsolete |
| **5** | معطل | Out of Service | Unsafe, no repair feasibility, no parts | NEVER auto-suggested (safety decision reserved for engineer) |

---

## Asset Management Classification (Your Document)

| Support Status | Definition | Manufacturer Status | Spare Parts | TRC Likely |
|---|---|---|---|---|
| **Supported / Active** | Active support, updates, training, parts available | Current production, actively marketed | ✅ Available | TRC 1–2 |
| **Limited Supported (Legacy)** | Equipment discontinued but support remains | No longer marketed; support contracts may exist | ⚠️ Limited | TRC 2–3 |
| **EOL (End of Life)** | Manufacturer ended routine support | Discontinued; support may be available through agents | ⚠️ Difficult | TRC 3–4 |
| **Obsolete** | Should replace: age, support gaps, tech advancement, regulatory risk | Support ended; no commitment to parts | ❌ Unavailable | TRC 4–5 |

---

## Decision Tree: What TRC Should a Device Get?

```
START: Device enters review
│
├─ Is device UNSAFE or parts completely unavailable?
│  └─ YES → TRC 5 (out of service)
│           [MANUAL DECISION ONLY — never auto-suggested]
│
├─ Is device OBSOLETE per manufacturer?
│  └─ YES → TRC 4 (working but unreliable)
│
├─ Does device have HIGH downtime (>50%) OR HIGH cost (>50%)?
│  └─ YES → TRC 4 (working but unreliable)
│
├─ Does device have MODERATE downtime (≤50%) + MODERATE cost (≤50%)?
│  └─ YES → Continue to TRC 3 checks
│
├─ Is support status "Supported/Active" OR "Limited Supported"?
│  └─ NO (support=EOL or Obsolete)
│       → If downtime <50% + cost <50% → TRC 3 (supported but limited)
│       → If downtime >50% or cost >50% → TRC 4
│
├─ Is device RECENT (<7yr) + LOW downtime (<20%) + LOW cost (<20%)?
│  └─ YES and support=Supported/Active → Candidate for TRC 2
│       └─ Check: Does device have certified quality certificate?
│           ├─ YES → TRC 2 (dependable)
│           └─ NO → TRC 3 (grey zone; review manually)
│
├─ Is device VERY RECENT (<3yr) + FULLY FUNCTIONAL + CERTIFIED?
│  └─ YES and support=Supported/Active → TRC 1 (latest, most reliable)
│
└─ Otherwise → TRC 3 (default; flag for review)
```

---

## Quick Lookup: Which TRC Should My Device Be?

**Use this if you want to quickly estimate without running the tool:**

### My device is...

**"...brand new (< 2 years old), works perfectly, I have the cert of quality"**
→ **TRC 1** (if manufacturer still makes it)
→ **TRC 2** (if out of production but supported)

**"...3–7 years old, mostly works, maintenance log shows <20% downtime and <20% cost"**
→ **TRC 2** (if supported by manufacturer)
→ **TRC 3** (if support is limited or EOL)

**"...more than 7 years old, generally reliable, spare parts available"**
→ **TRC 3** (if downtime <50% and cost <50%)
→ **TRC 4** (if downtime >50% or cost >50%)

**"...production discontinued, difficult to find parts, fails frequently"**
→ **TRC 4** (unreliable; plan replacement)

**"...broken, unsafe, no spare parts anywhere"**
→ **TRC 5** (out of service; replace immediately)

---

## Data Inputs Required for Auto-Suggestion

When you log maintenance or add a device, provide:

| Field | Example | Impact on TRC |
|-------|---------|---|
| **Device Code** | A41 | Links to maintenance history |
| **Brand / Model** | Atom Rabee Incu i | Determines expected life years |
| **Year of Production** | 2015 | Calculates age |
| **Status** | FF / PF / NF | FF better than PF/NF |
| **Certified** (NEW) | Yes / No | Required for TRC 1 eligibility |
| **Support Status** (NEW) | Supported/Active, Limited, EOL, Obsolete | Drives TRC 3 vs 4 distinction |
| **Maintenance Events** | Repairs, downtime, cost | Calculated metrics for TRC 2/3/4 |

---

## Common Questions

### Q: Can a device jump from TRC 4 to TRC 2?
**A:** Only if circumstances change significantly:
- Manufacturer restarts support (unlikely)
- Downtime history improves dramatically (requires good maintenance data)
- Device is replaced/refurbished

Typically: TRC 4 → TRC 3 (if support returns) → TRC 2 (if time passes + maintained well)

### Q: Why can TRC 1 never be suggested if age > 3 years?
**A:** Document criteria states TRC 1 requires "latest production from manufacturer, less than 3 years old." If production stopped or device is older, it's TRC 2 at best (if still supported).

### Q: What if downtime is exactly 20% (not <20%)?
**A:** Treat as threshold boundary. Current implementation uses `<` (strict), so 20% downtime = does NOT qualify for TRC 2, must be TRC 3 or lower.

### Q: Can I manually override the suggested TRC?
**A:** Yes. Suggested TRC is advisory. You can manually set any TRC 1–5 based on engineering judgment (especially TRC 5, which is never auto-suggested).

### Q: What if I don't know the support status?
**A:** Default to "Supported/Active" (most optimistic). Update later when you learn the device is discontinued or EOL.

---

## Maintenance Thresholds (From DOC-20260501-WA0011)

Keep these numbers in mind when maintaining devices:

| Metric | TRC 1 | TRC 2 | TRC 3 | TRC 4+ |
|--------|-------|-------|-------|---------|
| **Age** | < 3yr | < 7yr | Any | Usually > 10yr |
| **Downtime %** | Minimal | < 20% | < 50% | > 50% ⚠️ |
| **Cost Ratio** | Minimal | < 20% | < 50% | > 50% ⚠️ |
| **Support** | Active | Active | Active or Limited | Limited/None |
| **Certified** | Required | Recommended | Optional | No |

**Target:** Keep devices in TRC 2 (reliable, supported). Devices drifting to TRC 3+ need attention.

---

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-13 | Created; mapped Asset Classification ↔ TRC ↔ Data Fields |
