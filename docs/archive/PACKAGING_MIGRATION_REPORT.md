# PACKAGING MIGRATION REPORT

## Packaging Highlights
- `pyproject.toml` updated to standard `[tool.setuptools.packages.find] where = ['src']`.
- Console scripts configured:
  - `brjarvis = brjarvis.apps.cli:main`
  - `jarvis = brjarvis.apps.bootstrap:main`
  - `jarvis-cli = brjarvis.apps.cli:main`
  - `jarvis-server = brjarvis.apps.web:main`
- `setup.py` updated to package `src` with `package_dir={'': 'src'}`.
