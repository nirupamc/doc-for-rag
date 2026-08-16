#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('docs/research-log.md', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('### Test Coverage')
if idx >= 0:
    # Find the --- before it
    last_dash = content.rfind('---', 0, idx)
    if last_dash >= 0:
        # Insert after the ---
        new_section = u'''\n### M5 Recovery

**M5 Recovery Phase (2026-08-15)**

Recovered from upstream 502 error that interrupted previous session. Key fixes applied:

1. **Problem 1 -- Incorrect HeadingEvidence import**: `HeadingEvidence` was defined locally in `page_analyzer.py`, but interrupted code attempted `from ragparser.structure.signals import HeadingEvidence`. Removed the incorrect import; the local class is used directly.

2. **Problem 2 -- Duplicate method**: `_estimate_body_font_size()` was defined twice inside `PageStructureAnalyzer`. Kept the implementation with docstring (lines 75-84) and removed the duplicate.

3. **Problem 3 -- Enum/string inconsistency**: Mixed `BlockRole.UNKNOWN` with raw strings "unknown", "heading", "paragraph". Fixed all comparisons to use `BlockRole` enum consistently throughout.

**Additional fix -- Isolation edge case**: `_compute_isolation()` returned `inf` when a single block existed (no other blocks to compute gap against), which incorrectly counted as a heading signal. Fixed by tracking whether any other blocks were found; if not, return `0.0`.

**Tests added**: 21 new M5 tests in `tests/test_structure.py` covering `HeadingEvidence`, heading detection gates, body font size estimation, font aggregation, and enum/string consistency. All 142 tests pass (121 M1-M4 + 21 M5), 2 skipped.

**Stability**: Full test suite runs successfully with no regressions in M1--M4 behavior.

'''
        before = content[:last_dash+3]  # include the ---
        after = content[last_dash+3:]
        new_content = before + new_section + after
        with open('docs/research-log.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Research log updated successfully')
    else:
        print('Could not find --- before Test Coverage')
else:
    print('Could not find Test Coverage')