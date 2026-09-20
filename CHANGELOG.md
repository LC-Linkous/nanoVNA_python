# Changelog

All notable changes to nvnapython are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

Work on the current development branch. Entries move to a versioned section on
release.

### Added
- Continuous integration: a Tests workflow running the hardware-free suite
  (295 tests) across Windows, Linux, and macOS on Python 3.10–3.13, plus
  ruff, mypy, and package-build gates on every push and PR — the suite
  previously only ran locally. Coverage is gated at **85% minimum**
  (measured ~90% at adoption).
- Repository and packaging polish, ported from the hackrfpy/tsapython
  hardening passes: `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`
  (with the coverage-and-platform policy and PR expectations), a
  `.gitattributes` line-ending policy (LF everywhere, binaries protected),
  PyPI metadata (`Homepage` and `Changelog` project URLs, `keywords`,
  richer classifiers), a `dev` dependency group blessing `uv sync` /
  `uv run` as the workflow, and this changelog.
- Ruff configured with the family blocking ruleset (`E9 + F + W`);
  pre-existing whitespace findings fixed, plus one dead assignment a new
  `F` finding exposed in the tests. Mypy gated at basic strictness — the
  full-annotation pass that makes the shipped `py.typed` marker's promise
  true (`--disallow-untyped-defs` currently reports 145 errors) is a
  planned, separate project, as it was for tsapython.

### Changed
- The manual diagnostic scripts (`diagnose_continuous.py`,
  `diagnose_fastcmd.py`, `diagnose_help.py`, `collect_readme_data.py`)
  moved from `tests/` into `tests/diagnostics/`, with their package-path
  resolution updated for the new depth. They are hardware-in-hand dev
  tools, not part of the pytest suite.

## [2.0.0] and earlier

See the [GitHub releases](https://github.com/LC-Linkous/nanoVNA_python/releases)
for prior history.

[Unreleased]: https://github.com/LC-Linkous/nanoVNA_python/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/LC-Linkous/nanoVNA_python/releases/tag/v2.0.0
