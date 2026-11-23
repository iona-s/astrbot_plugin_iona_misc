# Tests

Run the suite from the plugin directory:

```text
python -m pytest
```

The unit tests use small fakes for AstrBot events. `test_pipeline.py` runs
`tests/astrbot_pipeline_smoke.py` in a clean process: it loads AstrBot's built-in
`astrbot` star and this plugin through the real plugin manager, then sends events
through the real `WakingCheckStage` to check that blocked senders stop there and
everyone else still reaches the built-in group context handlers.

The smoke script also runs on its own against any AstrBot install, for example
inside the AstrBot Docker image:

```text
python -m tests.astrbot_pipeline_smoke
```
