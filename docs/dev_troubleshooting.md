# Different Errors and how to handle then
## Celery
### `RuntimeError: Contract breach: app not finalized` when using celery chain
Make sure you imported all tasks used in chain ina core.py
```python
from server.pipeline.simulation import tasks as simulation_tasks
from server.pipeline.cli import tasks as simbad_cli_task
from server.pipeline.analyzer import tasks as simbad_analyzer_task
...
configure_celery(app, simulation_tasks.celery)
configure_celery(app, simbad_cli_task.celery)
configure_celery(app, simbad_analyzer_task.celery)
```