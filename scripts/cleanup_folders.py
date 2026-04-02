#!/usr/bin/env python3
"""Delete old ui_dist and ui folders"""
import shutil
import os

BASE = '/Users/asankhua/Cursor/Trail/M3- 8 april'

# Delete original ui_dist at root
old_ui_dist = os.path.join(BASE, 'ui_dist')
if os.path.exists(old_ui_dist):
    shutil.rmtree(old_ui_dist)
    print('✓ Deleted original ui_dist/')
else:
    print('✗ ui_dist/ not found')

# Delete ui folder (React/TypeScript source)
ui_folder = os.path.join(BASE, 'ui')
if os.path.exists(ui_folder):
    shutil.rmtree(ui_folder)
    print('✓ Deleted ui/')
else:
    print('✗ ui/ not found')

print('\nDone!')
