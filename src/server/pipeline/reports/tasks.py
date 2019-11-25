import datetime
import logging
import os
from os.path import join, isfile
from typing import List

from celery import Celery, chain, group, chord
from celery.result import AsyncResult

from database import db_session
from models.simulation import Artifact, SimulationStep, Simulation
from server.pipeline.reports.plots.mullerplot_histogram_matplotlib import histogram_plots
from server.pipeline.reports.plots.mutation_histogram import histogram_plot as mutation_histogram_plot
from server.pipeline.reports.plots.mutation_tree_plot import mutation_tree_plot
from server.pipeline.reports.plots.mullerplot_matplotlib import muller_plots

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
def reports_step(self, simulation_id: int) -> None:
    print("Run")
    start_time = datetime.datetime.utcnow()

    simulation: Simulation = db_session.query(Simulation).get(simulation_id)
    step: SimulationStep = SimulationStep(started_utc=start_time, origin="REPORT", simulation_id=simulation.id)
    db_session.flush()

    workdir: str = simulation.workdir
    output_path: str = workdir + "/plots/"

    if not os.path.exists(output_path):
        os.makedirs(output_path)

    simulation.current_step = "REPORT"
    simulation.current_step = step.id

    db_session.begin()
    db_session.add_all([simulation, step])
    db_session.commit()

    result = chain(
        all_clones_plot_stats.s(workdir),
        all_clones_mullerplot.s(),
        noise_plot_stats.s(),
        noise_mullerplot.s(),
        major_clones_plot_stats.s(),
        major_clones_mullerplot.s(),
        mullerplot.s(),
        mutation_tree.s(),
        mutation_histogram.s(),
        save_result.s(simulation_id, step.id, workdir)
    ).apply_async()
    return result


@celery.task(bind=True, name='SIMBAD-ALL-CLONES-PLOTS-STATS')
def all_clones_plot_stats(self, workdir: str):
    print(workdir)
    input_file: str = workdir + "/output_data/clone_stats_scalars.parquet"
    time_file: str = workdir + "/output_data/time_points.parquet"

    output_path: str = workdir + "/plots/"

    plot_stats(input_file, time_file, output_path)
    return workdir


@celery.task(bind=True, name='SIMBAD-ALL-CLONES-MULLERPLOT-STATS')
def all_clones_mullerplot(self, workdir: str):
    param_names = [
        'birthEfficiency',
        'birthResistance',
        'lifespanEfficiency',
        'lifespanResistance',
        'successEfficiency',
        'successResistance',
    ]
    tasks = []
    for name in param_names:
        tasks.append(all_clones_mullerplot_histogram.s(workdir, name))
    chord(tasks, chordfinisher.si()).apply_async()
    return workdir


@celery.task(bind=True, name='ALL-CLONES-MULLERPLOT-HISTOGRAM')
def all_clones_mullerplot_histogram(self, workdir: str, param_name: str):
    input_csv_file = "{}/output_data/histogram_{}.csv".format(workdir, param_name)
    time_parquet = "{}/output_data/time_points.parquet".format(workdir)
    stats_parquet = "{}/output_data/clone_stats_scalars.parquet".format(workdir)
    output_file = "{}/plots/histogram-{}".format(workdir, param_name)
    print('mullerplot_histogram in {} for {}'.format(workdir, param_name))
    histogram_plots(input_csv_file, param_name, time_parquet, stats_parquet, output_file)


@celery.task(bind=True, name='SIMBAD-NOISE-PLOTS-STATS')
def noise_plot_stats(self, workdir: str):
    print(workdir)
    input_file: str = workdir + "/output_data/noise_stats_scalars.parquet"
    time_file: str = workdir + "/output_data/time_points.parquet"
    output_path: str = workdir + "/plots/noise-"
    plot_stats(input_file, time_file, output_path)
    return workdir


@celery.task(bind=True, name='SIMBAD-NOISE-MULLERPLOT-STATS')
def noise_mullerplot(self, workdir: str):
    param_names = [
        'birthEfficiency',
        'birthResistance',
        'lifespanEfficiency',
        'lifespanResistance',
        'successEfficiency',
        'successResistance',
    ]

    tasks = []
    for name in param_names:
        tasks.append(noise_mullerplot_histogram.s(workdir, name))
    chord(tasks, chordfinisher.si()).apply_async()
    return workdir


@celery.task(bind=True, name='NOISE-MULLERPLOT-HISTOGRAM')
def noise_mullerplot_histogram(self, workdir: str, param_name: str):
    input_csv_file = "{}/output_data/noise_histogram_{}.csv".format(workdir, param_name)
    time_parquet = "{}/output_data/time_points.parquet".format(workdir)
    stats_parquet = "{}/output_data/noise_stats_scalars.parquet".format(workdir)
    output_file = "{}/plots/noise-histogram-{}".format(workdir, param_name)
    print('mullerplot_histogram in {} for {}'.format(workdir, param_name))
    histogram_plots(input_csv_file, param_name, time_parquet, stats_parquet, output_file)


@celery.task(bind=True, name='SIMBAD-MAJOR-CLONES-PLOTS-STATS')
def major_clones_plot_stats(self, workdir: str):
    print(workdir)
    input_file: str = workdir + "/output_data/major_stats_scalars.parquet"
    time_file: str = workdir + "/output_data/time_points.parquet"
    output_path: str = workdir + "/plots/major-"
    plot_stats(input_file, time_file, output_path)
    return workdir


@celery.task(bind=True, name='SIMBAD-MAJOR-CLONES-MULLERPLOT-STATS')
def major_clones_mullerplot(self, workdir: str):
    param_names = [
        'birthEfficiency',
        'birthResistance',
        'lifespanEfficiency',
        'lifespanResistance',
        'successEfficiency',
        'successResistance',
    ]

    tasks = []
    for name in param_names:
        tasks.append(major_clones_mullerplot_histogram.s(workdir, name))
    chord(tasks, chordfinisher.si()).apply_async()
    return workdir


@celery.task(bind=True, name='MAJOR-CLONES-MULLERPLOT-HISTOGRAM')
def major_clones_mullerplot_histogram(self, workdir: str, param_name: str):
    input_csv_file = "{}/output_data/major_histogram_{}.csv".format(workdir, param_name)
    time_parquet = "{}/output_data/time_points.parquet".format(workdir)
    stats_parquet = "{}/output_data/major_stats_scalars.parquet".format(workdir)
    output_file = "{}/plots/major-histogram-{}".format(workdir, param_name)
    print('mullerplot_histogram in {} for {}'.format(workdir, param_name))
    histogram_plots(input_csv_file, param_name, time_parquet, stats_parquet, output_file)


@celery.task(bind=True, name='MULLERPLOT')
def mullerplot(self, workdir: str):
    input_file = "{}/output_data/muller_data.parquet".format(workdir)
    stats_file = "{}/output_data/clone_stats_scalars.parquet".format(workdir)
    params_file = "{}/output_data/large_clones.parquet".format(workdir)
    large_muller_order = "{}/output_data/large_muller_order.parquet".format(workdir)
    output_prefix: str = workdir + "/plots/muller_plot_"
    muller_plots(input_file, stats_file, params_file, large_muller_order, output_prefix)
    return workdir


@celery.task(bind=True, name='MUTATION-HISTOGRAM')
def mutation_histogram(self, workdir: str):
    input_file = "{}/output_data/large_final_mutations.parquet".format(workdir)
    threshold = 11
    output_file: str = workdir + "/plots/mutation_histogram.png"
    mutation_histogram_plot(input_file, threshold, output_file)
    return workdir


@celery.task(bind=True, name='MUTATION-TREE')
def mutation_tree(self, workdir: str):
    data_path = "{}/output_data/large_final_mutations.parquet".format(workdir)
    output_file: str = workdir + "/plots/mutation-tree.png"
    mutation_tree_plot(data_path, output_file)
    return workdir


@celery.task(name='SAVE-RESULT')
def save_result(plots, simulation_id: int, step_id: int, workdir: str):
    output_path: str = workdir + "/plots/"
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


@celery.task
def chordfinisher(*args, **kwargs):
    return "OK"
