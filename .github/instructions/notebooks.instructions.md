---
applyTo: "notebooks/**/*.ipynb"
---

## Notebook conventions

Each notebook answers exactly one research question stated in the first markdown cell.

Structure every notebook with these sections in order:
1. **Question** — one sentence, the research question this notebook answers
2. **Setup** — imports and data loading via `from src.data_loader import load_radnett, load_civil_defence, load_station_locations`
3. **Analysis** — code and narrative
4. **Key Findings** — bullet points of what was discovered
5. **Take-Home Message** — one sentence, decision-relevant for DSA leadership
6. **Acceptance Criteria** — checklist confirming the notebook delivered what was specified

Never re-implement data loading or cleaning. Always use `src/data_loader.py`.
Never hardcode file paths to raw data in notebooks.

Figures should be saved via `from src.utils import save_figure` and also displayed inline.

Keep code cells focused — one logical step per cell. Prefer showing intermediate results so the reader can follow the reasoning.

When comparing Radnett and Civil Defence data, always verify units are aligned (both in µSv/h).

When plotting station data on maps, use the color scheme from `src/utils.py` and always include Svalbard in the extent.
