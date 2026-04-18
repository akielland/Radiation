---
applyTo: "tests/**/*.py"
---

## Test conventions

Use pytest. Test files mirror the src module they test: `test_data_loader.py`, `test_schemas.py`, `test_utils.py`.

Key testing principles:
- Use small synthetic fixtures, not the full dataset files
- Test the data contracts: correct types, reasonable ranges, expected column names
- Test unit conversion: Civil Defence Sv/h → µSv/h
- Test coordinate parsing: WKT POINT format → separate lat/lon floats
- Test metadata extraction: rainfall flag, snow depth parsed correctly from dict-string
- Test that loading functions return expected shapes and dtypes
- Test edge cases: what happens with empty strings, malformed coordinates, missing metadata fields
- Test utility functions: uptime classification thresholds, figure saving

Tests should run without network access and without the real data files present.
