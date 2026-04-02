#!/usr/bin/env python3
"""Move ui_dist to frontend and delete ui folder"""
import shutil
import os

BASE = '/Users/asankhua/Cursor/Trail/M3- 8 april'

# Move ui_dist to frontend
src = os.path.join(BASE, 'ui_dist')
dst = os.path.join(BASE, 'frontend', 'ui_dist')

if os.path.exists(src):
    shutil.move(src, dst)
    print(f'✓ Moved ui_dist to frontend/')
else:
    print(f'✗ ui_dist not found at {src}')

# Delete ui folder
ui_folder = os.path.join(BASE, 'ui')
if os.path.exists(ui_folder):
    shutil.rmtree(ui_folder)
    print(f'✓ Deleted ui/ folder')
else:
    print(f'✗ ui/ folder not found')

print('\nDone!')
