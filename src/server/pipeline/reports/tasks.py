import datetime
import logging
import os
from os.path import join, isfile
from typing import List

from celery import Celery, chain
from celery.result import AsyncResult

from database import db_session
from models.simulation import Artifact, SimulationStep, Simulation
from server.pipeline.reports.plots.plot_stats import plot_stats

logger = logging.getLogger()
celery = Celery(__name__, autofinalize=False)


def index_plots(out_dir: str, simulation_id: int, step_id: int) -> List[Artifact]:
    """
    Get paths and file sizes of all plot images in directory
    :param simulation_id:
    :param step_id:
    :param out_dir:
    :return:
    """
    plot_file_names: List[str] = [f for f in os.listdir(out_dir) if isfile(join(out_dir, f))]
    plot_artifacts: list = []
    for plot_name in plot_file_names:
        plot_path = out_dir + "/" + plot_name
        plot_artifacts.append(
            Artifact(
                path=plot_path,
                size_kb=os.path.getsize(plot_path),
                simulation_id=simulation_id,
                step_id=step_id
            )
        )
    return plot_artifacts


@celery.task(bind=True, name='SIMBAD-PLOTS-MAIN')
def reports_step(self, simulation_id: int) -> AsyncResult:
    print("Run")
    start_time = datetime.datetime.utcnow()

    simulation: Simulation = db_session.query(Simulation).get(simulation_id)
    step: SimulationStep = SimulationStep(started_utc=start_time, origin="REPORT", simulation_id=simulation.id)
    db_session.flush()

    workdir: str = simulation.workdir
    simulation.current_step = "REPORT"
    simulation.current_step = step.id

    db_session.begin()
    db_session.add_all([simulation, step])
    db_session.commit()

    result = chain(
        run_plot_stats.s(simulation_id, step.id, workdir)
    ).apply_async()
    return result


@celery.task(bind=True, name='SIMBAD-PLOTS-STATS')
def run_plot_stats(self, simulation_id: int, step_id: int, workdir: str) -> (int, int, str):
    print(simulation_id, step_id, workdir)
    input_file: str = workdir + "/output_data/clone_stats_scalars.parquet"
    time_file: str = workdir + "/output_data/time_points.parquet"

    output_path: str = workdir + "/plots/"

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    plot_stats(input_file, time_file, output_path)
    plots: List[Artifact] = index_plots(output_path, simulation_id, step_id)
    simulation: Simulation = db_session.query(Simulation).get(simulation_id)
    step: SimulationStep = db_session.query(SimulationStep).get(step_id)
    db_session.flush()
    db_session.begin()
    end_time = datetime.datetime.utcnow()
    simulation.finished_utc = end_time
    step.finished_utc = end_time
    db_session.add_all(plots)
    db_session.add_all([simulation, step])
    db_session.commit()
    return simulation_id, step_id, workdir
