#!/usr/bin/env python3
"""Interactive script to register a new hospital/department facility.

Run from inside multi-facility-dashboard/:
    python3 add_facility.py
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import openpyxl

from build import HEADER_MAP, MAINT_LOG_NAME, clean

ROOT = Path(__file__).parent
CONFIG_PATH = ROOT / "config.json"
FACILITIES_DIR = ROOT / "data" / "facilities"


def ask(prompt, default=None, required=False):
    while True:
        suffix = f" [{default}]" if default else ""
        val = input(f"{prompt}{suffix}: ").strip()
        if not val and default is not None:
            return default
        if not val and required:
            print("  This field is required.")
            continue
        return val


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "_", text.strip().lower()).strip("_")


def validate_headers(path):
    wb = openpyxl.load_workbook(path, data_only=True)
    row = next(wb.worksheets[0].iter_rows(max_row=1, values_only=True))
    fields = [HEADER_MAP.get(clean(h)) for h in row]
    return "code" in fields


def main():
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    facilities = config.setdefault("facilities", {})
    known_categories = set(config.get("categories", {}).keys())

    print("=== Add a new hospital/department facility ===\n")

    while True:
        hospital_ar = ask("Hospital name (Arabic)", required=True)
        hospital_en = ask("Hospital name (English)", default=hospital_ar)
        dept_ar = ask("Department name (Arabic, optional)")
        dept_en = ask("Department name (English, optional)", default=dept_ar)

        suggested_key = slugify(f"{hospital_en}_{dept_en}" if dept_en else hospital_en)
        key = slugify(ask("Facility key (short slug, used as folder name)", default=suggested_key))
        if key == "main":
            print("  'main' is reserved for your own equipment. Choose another key.\n")
            continue
        if key in facilities:
            if ask(f"  Facility '{key}' already exists. Overwrite its registration? (y/n)", default="n").lower() != "y":
                continue
        break

    name_ar = f"{hospital_ar} — {dept_ar}" if dept_ar else hospital_ar
    name_en = f"{hospital_en} — {dept_en}" if dept_en else hospital_en
    meta = {"name_en": name_en, "name_ar": name_ar,
            "hospital_en": hospital_en, "hospital_ar": hospital_ar}
    if dept_en or dept_ar:
        meta["department_en"] = dept_en
        meta["department_ar"] = dept_ar

    facility_dir = FACILITIES_DIR / key
    facility_dir.mkdir(parents=True, exist_ok=True)
    print(f"\nFolder ready: {facility_dir}")
    print("Now add category Excel files (same header standard as your own fleet).")
    print("Filename should match a category key from config.json, e.g. incubators.xlsx\n")

    added_files = []
    while True:
        src = ask("Path to a category .xlsx file (blank to stop adding files)")
        if not src:
            break
        src_path = Path(src).expanduser()
        if not src_path.is_file() or src_path.suffix.lower() != ".xlsx":
            print("  Not a valid .xlsx file, try again.")
            continue
        if not validate_headers(src_path):
            print("  WARNING: this file's headers don't match the standard column layout "
                  f"(expected Arabic headers like {list(HEADER_MAP)}). Skipped.")
            continue
        dest = facility_dir / src_path.name.lower()
        shutil.copy(src_path, dest)
        added_files.append(dest.name)
        stem = dest.stem.lower()
        if stem not in known_categories:
            print(f"  Copied {dest.name}. NOTE: '{stem}' isn't in config.json -> categories yet - "
                  "it'll build with default life-expectancy/PM settings until you add proper config for it.")
        else:
            print(f"  Copied {dest.name}.")

    if not added_files:
        print("  No category files added - you can drop them into the folder later.")

    log_src = ask("\nPath to this facility's maintenance_log.xlsx (optional, blank to skip)")
    if log_src:
        log_path = Path(log_src).expanduser()
        if log_path.is_file():
            shutil.copy(log_path, facility_dir / MAINT_LOG_NAME)
            print("  Copied maintenance log.")
        else:
            print("  File not found, skipped.")

    facilities[key] = meta
    CONFIG_PATH.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRegistered facility '{key}' in config.json.")

    if ask("\nRebuild data.json now? (y/n)", default="y").lower() == "y":
        subprocess.run([sys.executable, "build.py"], cwd=ROOT, check=True)

    if ask("Publish now via ./update.sh (build + commit + push)? (y/n)", default="n").lower() == "y":
        subprocess.run(["./update.sh", f"Add facility: {name_en}"], cwd=ROOT, check=True)
    else:
        print("\nWhen ready: cd multi-facility-dashboard && ./update.sh")


if __name__ == "__main__":
    main()
