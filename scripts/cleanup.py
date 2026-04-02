#!/usr/bin/env python3
import os
import shutil
import glob
import sys

base_path = "/Users/asankhua/Cursor/Trail/M3- 8 april"

print(f"Starting cleanup in: {base_path}", flush=True)
print(f"Current directory: {os.getcwd()}", flush=True)

# Remove phase-5-testing-docs
phase5_path = os.path.join(base_path, "phase-5-testing-docs")
print(f"Checking: {phase5_path}", flush=True)
print(f"Exists: {os.path.exists(phase5_path)}", flush=True)

if os.path.exists(phase5_path):
    try:
        shutil.rmtree(phase5_path)
        print(f"✅ Removed: {phase5_path}", flush=True)
    except Exception as e:
        print(f"❌ Error removing {phase5_path}: {e}", flush=True)
        sys.exit(1)
else:
    print(f"⚠️ Not found: {phase5_path}", flush=True)

# Remove test files
test_patterns = ["*test*.py", "*debug*.py", "*mock*.py", "test_*.html"]
removed_count = 0

for pattern in test_patterns:
    pattern_path = os.path.join(base_path, pattern)
    files = glob.glob(pattern_path)
    print(f"Pattern {pattern}: found {len(files)} files", flush=True)
    for file in files:
        try:
            os.remove(file)
            print(f"✅ Removed: {os.path.basename(file)}", flush=True)
            removed_count += 1
        except Exception as e:
            print(f"❌ Error removing {file}: {e}", flush=True)

print(f"\n✅ Cleanup complete! Removed {removed_count} files", flush=True)
