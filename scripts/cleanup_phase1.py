#!/usr/bin/env python3
"""Cleanup phase-1-core-voice - remove unnecessary files"""
import os

files_to_remove = [
    'phase-1-core-voice/hf_pipeline.py',
    'phase-1-core-voice/requirements.txt',
]

dirs_to_remove = [
    'phase-1-core-voice/ui',
]

base = '/Users/asankhua/Cursor/Trail/M3- 8 april'

for f in files_to_remove:
    path = os.path.join(base, f)
    if os.path.exists(path):
        os.remove(path)
        print(f'✓ Removed: {f}')
    else:
        print(f'✗ Not found: {f}')

for d in dirs_to_remove:
    path = os.path.join(base, d)
    if os.path.exists(path) and os.path.isdir(path):
        os.rmdir(path)
        print(f'✓ Removed dir: {d}')
    else:
        print(f'✗ Not found: {d}')

print('\nDone!')
