# AGENTS.md

## Scope

These instructions apply to the entire repository.

This project is a personal AstrBot plugin that collects small, deployment-specific
adjustments which do not justify a plugin of their own. It is installed from
GitHub, not from the plugin marketplace. Each adjustment is a self-contained
feature with its own module and configuration section.

## Working Rules

- Inspect the working tree before editing and preserve unrelated user changes.
- Keep implementation changes narrowly scoped and follow existing module boundaries.
- Do not commit generated caches, local configuration, or plugin runtime state.
- Do not commit, push, tag, or publish a release unless explicitly requested.

## Repository Structure

- `main.py` is the AstrBot loader shim. Runtime implementation belongs under `core/`.
- `core/plugin.py` owns framework registration, lifecycle, hooks, and commands.
- `core/config.py` owns configuration parsing; `_conf_schema.json` defines the
  AstrBot-facing configuration form, with one object section per feature.
- `core/sender_block.py` owns the sender blocklist and its wake-up check filter.
- A new feature gets its own `core/<feature>.py` module and config section.

## Compatibility

- Target Python `>=3.12,<4` and AstrBot `>=4.28,<5`. The deployment follows
  `soulter/astrbot:latest` automatically, so prefer public plugin APIs and avoid
  patching AstrBot internals.
- Sender blocking relies on two pipeline behaviors: handler filters run in
  `WakingCheckStage`, and the scheduler ends the pipeline after any stage that
  stops the event. `tests/astrbot_pipeline_smoke.py` checks both against the
  installed AstrBot together with the built-in `astrbot` star; keep it passing.
- The sender block handler priority must stay above every built-in handler
  priority (currently up to `sys.maxsize`).

## Configuration And State

- Treat configuration as untrusted input and normalize it at the configuration
  boundary. When configuration changes, update the parser, schema, README, and
  changelog together.
- Keep account IDs and other deployment data in plugin configuration, never in
  the source tree; the repository is public.
- Persist state only under AstrBot's plugin data directory, never in the source tree.

## Quality Checks

```text
ruff check --config ruff.toml .
ruff format --check --config ruff.toml .
python -m compileall -q main.py core
python -m pytest
```

## Documentation And Release Hygiene

- Keep `README.md`, `metadata.yaml`, `_conf_schema.json`, and `CHANGELOG.md`
  synchronized with public behavior, and keep the metadata version aligned with
  the leading changelog release heading.
- Use Conventional Commit subjects without scopes.
