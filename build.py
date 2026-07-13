#!/usr/bin/env python3
"""Build site/data.json from the Excel inventory files in data/.

Each .xlsx in data/ is one equipment category (filename = category key in
config.json). Sheets must follow the standard INC.xlsx column layout:

    الماركة | الموديل | الرقم المسلسل | الكود | تاريخ الانتاج | TRC | الحالة الفنية | وصف الحالة الفنية
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import openpyxl

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
OUT_FILE = ROOT / "site" / "data.json"

CURRENT_YEAR = datetime.now().year

# Column header -> field name (headers as they appear in the standard sheet)
HEADER_MAP = {
    "الماركة": "brand",
    "الموديل": "model",
    "الرقم المسلسل": "serial",
    "الكود": "code",
    "تاريخ الانتاج": "year",
    "TRC": "trc",
    "الحالة الفنية": "status",
    "وصف الحالة الفنية": "description",
}

STATUS_RANK = {"NF": 3, "PF": 2, "FF": 1}

# Spare-part patterns, most specific first. Each: (part_key, regex)
PART_PATTERNS = [
    ("humidifier_door_lock", r"لوك\s+باب\s+المرطب"),
    ("humidifier_door", r"باب\s+المرطب"),
    ("humidifier", r"المرطب"),
    ("window_lock", r"لوك\s+شباك"),
    ("door_lock", r"لوك\s+باب"),
    ("window", r"شباك"),
    ("hood", r"hood"),
    ("door", r"باب|الابواب|الأبواب"),
    ("control_board", r"بوردة\s+الكنترول|بورده\s+الكنترول"),
    ("motor", r"الماتور|ماتور"),
    ("heater", r"heater|الهيتر"),
    ("keypad", r"stuck\s*key"),
    ("monitor_mount", r"حامل\s+الشاشة"),
]

PART_NAMES = {
    "window":               {"en": "Porthole window",        "ar": "شباك"},
    "window_lock":          {"en": "Porthole window lock",   "ar": "لوك شباك"},
    "door":                 {"en": "Access door",            "ar": "باب"},
    "door_lock":            {"en": "Access door lock",       "ar": "لوك باب"},
    "humidifier":           {"en": "Humidifier unit",        "ar": "وحدة الترطيب (المرطب)"},
    "humidifier_door":      {"en": "Humidifier door",        "ar": "باب المرطب"},
    "humidifier_door_lock": {"en": "Humidifier door lock",   "ar": "لوك باب المرطب"},
    "hood":                 {"en": "Hood (canopy)",          "ar": "الغطاء (hood)"},
    "control_board":        {"en": "Control board",          "ar": "بوردة الكنترول"},
    "motor":                {"en": "Motor",                  "ar": "الماتور"},
    "heater":               {"en": "Heater",                 "ar": "الهيتر (heater)"},
    "keypad":               {"en": "Keypad / membrane keys", "ar": "لوحة المفاتيح"},
    "monitor_mount":        {"en": "Monitor mount fixing",   "ar": "حامل الشاشة"},
}

# TRC criteria from the organization's classification document (DOC-20260501-WA0011)
TRC_CRITERIA = [
    {
        "trc": 1,
        "verdict_ar": "يعمل ويعتمد عليه",
        "verdict_en": "Working and dependable",
        "criteria_ar": [
            "أحدث إنتاج للشركة المصنعة ولم يمر على إنتاجه أكثر من 3 سنوات ويعمل بكفاءة وحاصل على شهادة جودة معتمدة",
        ],
        "criteria_en": [
            "Latest production from the manufacturer, less than 3 years old, working efficiently, with a certified quality certificate",
        ],
    },
    {
        "trc": 2,
        "verdict_ar": "يعمل ويعتمد عليه",
        "verdict_en": "Working and dependable",
        "criteria_ar": [
            "حديث نسبياً لم يمر على إنتاجه أكثر من 7 سنوات",
            "يوجد له دعم فني من الشركة المصنعة والوكيل المعتمد",
            "أعطال الجهاز لا تتخطى 20% من السنة والتكلفة التراكمية لا تزيد عن 20% عن الجهاز المماثل",
            "الجهاز يستخدم بصورة أساسية ويعتمد عليه",
        ],
        "criteria_en": [
            "Relatively recent, less than 7 years since production",
            "Technical support available from manufacturer and authorized agent",
            "Downtime under 20% per year; cumulative cost under 20% of an equivalent device",
            "Used as primary equipment and relied upon",
        ],
    },
    {
        "trc": 3,
        "verdict_ar": "يعمل ويعتمد عليه",
        "verdict_en": "Working and dependable",
        "criteria_ar": [
            "توقف إنتاجه ولكن يوجد له دعم فني من الشركة المصنعة والوكيل المعتمد",
            "التكلفة التراكمية للجهاز لا تزيد عن 50% من سعر الجهاز",
            "نسبة الأعطال (Down time) لا تتخطى الـ 50%",
        ],
        "criteria_en": [
            "Production discontinued, but technical support still available from manufacturer and agent",
            "Cumulative cost under 50% of the device price",
            "Downtime does not exceed 50%",
        ],
    },
    {
        "trc": 4,
        "verdict_ar": "يعمل ولكن لا يعتمد عليه بصورة أساسية",
        "verdict_en": "Working but not dependable as primary equipment",
        "criteria_ar": [
            "توقف إنتاجه ولا يوجد له دعم فني أو قطع غيار من الشركة المصنعة والوكيل المعتمد",
            "لا يمكن الاعتماد عليه بصورة أساسية",
            "كثير الأعطال ونسبة الأعطال (Down time) تتخطى الـ 50%",
            "التكلفة التراكمية للجهاز تزيد عن 50% من سعر الجهاز",
        ],
        "criteria_en": [
            "Production discontinued; no technical support or spare parts from manufacturer or agent",
            "Cannot be relied upon as primary equipment",
            "Frequent failures; downtime exceeds 50%",
            "Cumulative cost exceeds 50% of the device price",
        ],
    },
    {
        "trc": 5,
        "verdict_ar": "معطل",
        "verdict_en": "Out of service",
        "criteria_ar": [
            "غير آمن",
            "لا جدوى فنية أو اقتصادية من إصلاحه",
            "مستلزمات التشغيل أو قطع الغيار والأكسسوارات الأساسية غير متوفرة",
        ],
        "criteria_en": [
            "Unsafe",
            "No technical or economic feasibility of repair",
            "Operating supplies, spare parts, and essential accessories unavailable",
        ],
    },
]


def clean(v):
    if v is None:
        return ""
    return str(v).strip()


def parse_year(v):
    m = re.search(r"(19|20)\d{2}", clean(v))
    return int(m.group(0)) if m else None


def parse_faults(description):
    """Split multi-line fault description into individual fault strings."""
    lines = [ln.strip() for ln in clean(description).splitlines()]
    return [ln for ln in lines if ln]


def extract_parts(fault_line):
    """Detect needed spare parts (with quantity) in one Arabic fault line."""
    found = []
    remaining = fault_line
    for key, pattern in PART_PATTERNS:
        m = re.search(pattern, remaining, re.IGNORECASE)
        if not m:
            continue
        qty = 1
        # quantity forms: "عدد (2) شباك", "عدد (2)شباك", "2 شباك", "تحتاج 3 شباك"
        prefix = remaining[: m.start()]
        qm = re.search(r"عدد\s*\(?\s*(\d+)\s*\)?\s*$", prefix) or re.search(r"(\d+)\s*$", prefix)
        if qm:
            qty = int(qm.group(1))
        found.append({"part": key, "qty": qty})
        # remove the matched text so broader patterns (شباك after لوك شباك) don't double-count
        remaining = remaining[: m.start()] + remaining[m.end():]
    return found


def score_device(trc, status, age, expected_life):
    """Explainable 0-100 replacement priority score."""
    trc = trc or 3
    score = trc * 15
    score += {"NF": 20, "PF": 8}.get(status, 0)
    if age is not None and expected_life:
        score += min(age / expected_life, 1.5) * 10
    score = min(round(score), 100)

    if trc == 5 or score >= 80:
        rec = "replace_now"
    elif score >= 65:
        rec = "plan_replacement"
    elif score >= 40:
        rec = "monitor"
    else:
        rec = "ok"
    return score, rec


def read_category(path, cat_cfg, default_life):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    headers = [clean(h) for h in next(rows)]
    fields = [HEADER_MAP.get(h) for h in headers]
    if "code" not in fields:
        sys.exit(f"ERROR: {path.name}: sheet does not follow the standard column layout "
                 f"(expected Arabic headers like {list(HEADER_MAP)})")

    expected_life = cat_cfg.get("expected_life_years", default_life)
    devices = {}
    for row in rows:
        rec = {f: clean(v) for f, v in zip(fields, row) if f}
        if not any(rec.values()):
            continue
        code = rec.get("code") or f"?{len(devices)+1}"
        year = parse_year(rec.get("year"))
        trc = int(m.group(0)) if (m := re.search(r"[1-5]", rec.get("trc", ""))) else None
        status = rec.get("status", "").upper()
        faults = parse_faults(rec.get("description"))

        if code in devices:
            # same device listed twice: merge faults, keep worst TRC/status
            d = devices[code]
            d["faults"] += [f for f in faults if f not in d["faults"]]
            if trc and trc > (d["trc"] or 0):
                d["trc"] = trc
            if STATUS_RANK.get(status, 0) > STATUS_RANK.get(d["status"], 0):
                d["status"] = status
            continue

        devices[code] = {
            "code": code,
            "brand": rec.get("brand", ""),
            "model": rec.get("model", ""),
            "serial": rec.get("serial", ""),
            "year": year,
            "trc": trc,
            "status": status,
            "faults": faults,
        }

    result = []
    for d in devices.values():
        age = (CURRENT_YEAR - d["year"]) if d["year"] else None
        d["age"] = age
        d["expected_life"] = expected_life
        parts = []
        for fl in d["faults"]:
            parts += extract_parts(fl)
        d["parts_needed"] = parts
        d["score"], d["recommendation"] = score_device(d["trc"], d["status"], age, expected_life)
        result.append(d)

    result.sort(key=lambda d: -d["score"])
    return result


def category_stats(devices, expected_life):
    n = len(devices)
    by_status = {"FF": 0, "PF": 0, "NF": 0}
    by_trc = {}
    by_rec = {"replace_now": 0, "plan_replacement": 0, "monitor": 0, "ok": 0}
    ages = []
    past_life = 0
    for d in devices:
        if d["status"] in by_status:
            by_status[d["status"]] += 1
        if d["trc"]:
            by_trc[str(d["trc"])] = by_trc.get(str(d["trc"]), 0) + 1
        by_rec[d["recommendation"]] += 1
        if d["age"] is not None:
            ages.append(d["age"])
            if d["age"] >= expected_life:
                past_life += 1
    parts_total = {}
    for d in devices:
        for p in d["parts_needed"]:
            e = parts_total.setdefault(p["part"], {"qty": 0, "devices": []})
            e["qty"] += p["qty"]
            if d["code"] not in e["devices"]:
                e["devices"].append(d["code"])
    return {
        "total": n,
        "by_status": by_status,
        "by_trc": dict(sorted(by_trc.items())),
        "by_recommendation": by_rec,
        "avg_age": round(sum(ages) / len(ages), 1) if ages else None,
        "past_expected_life": past_life,
        "past_expected_life_pct": round(100 * past_life / len(ages)) if ages else None,
        "parts_needed": dict(sorted(parts_total.items(), key=lambda kv: -kv[1]["qty"])),
    }


def main():
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    default_life = config.get("default_expected_life_years", 10)
    categories = {}
    for path in sorted(DATA_DIR.glob("*.xlsx")):
        key = path.stem.lower()
        cat_cfg = config["categories"].get(key, {})
        devices = read_category(path, cat_cfg, default_life)
        stats = category_stats(devices, cat_cfg.get("expected_life_years", default_life))
        categories[key] = {
            "name_en": cat_cfg.get("name_en", key.title()),
            "name_ar": cat_cfg.get("name_ar", key),
            "expected_life_years": cat_cfg.get("expected_life_years", default_life),
            "life_note_en": cat_cfg.get("life_note_en", ""),
            "life_note_ar": cat_cfg.get("life_note_ar", ""),
            "stats": stats,
            "devices": devices,
        }
        print(f"{path.name}: {stats['total']} devices "
              f"(FF {stats['by_status']['FF']} / PF {stats['by_status']['PF']} / NF {stats['by_status']['NF']})")

    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_year": CURRENT_YEAR,
        "part_names": PART_NAMES,
        "trc_criteria": TRC_CRITERIA,
        "categories": categories,
    }
    OUT_FILE.parent.mkdir(exist_ok=True)
    OUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUT_FILE} ({OUT_FILE.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
