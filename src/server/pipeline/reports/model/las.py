import subprocess

import laspy
import matplotlib as mpl
import matplotlib.cm as cm
import numpy as np
import pandas as pd
from pandas import DataFrame


def stream_to_las(stream_path: str, parameter_name: str, out_path: str) -> None:
    """
    Create lidar .las file from simulation stream file, with cell X,Y,Z positions
    and given parameter mapped to color
    :param out_path:
    :param stream_path:
    :param parameter_name:
    :return:
    """
    df = pd.read_csv(stream_path, sep=';')
    if parameter_name in df.columns:
        x = df['position_0']
        y = df['position_1']
        z = df['position_2']

        """
        In contrast to lidarview -> http://lidarview.com/ Potree seems to require additional data
        in the header, mainly the offset and scale arrays, to display the .las files correctly.
        More precisely, not the Potree, but the Entwine converter that generates files recognizable by Potree.
        This change was made as the Entwine converter throws error "Bounds are too large for the selected scale "
        if those values are not supplied.
        There's little documentation from laspy how to create new .las file and fill it with data, and the values in
        header may need to be adjusted later, as i have no idea what they really do.
        Example -> https://github.com/laspy/laspy/commit/4dba4c846eacf119b5e99ccf8ccae73735ef1944
        The point_format=2 is needed for RGB colouring of points.
        """
        header = laspy.header.Header(point_format=2)
        outfile = laspy.file.File(out_path, mode="w", header=header)

        x_min = np.floor(np.min(x))
        y_min = np.floor(np.min(y))
        z_min = np.floor(np.min(z))

        outfile.header.offset = [x_min, y_min, z_min]
        outfile.header.scale = [0.1, 0.1, 0.1]

        outfile.x = x
        outfile.y = y
        outfile.z = z

        parameter_series = df[parameter_name]
        r, g, b = map_to_colors(parameter_series)

        outfile.red = r
        outfile.green = g
        outfile.blue = b
        outfile.close()
    else:
        print('Parameter {} does not exist in file'.format(parameter_name))
    return


def map_to_colors(series: DataFrame) -> (DataFrame, DataFrame, DataFrame):
    """
    Map series of parameter values to RGB colors
    :param series:
    :return: the tuple of (R, G, B) DataFrame values
    """
    mapper = build_color_mapper(series)

    # list comprehension is not used here so that numpy can vectorize the mapper calls
    colors = mapper.to_rgba(series)
    r, g, b, a = colors.T

    # matplotlib mapper returns RGBA values in 0.0-1.0 range format, and .las files (or maybe potree viewer)
    # seem to require color in 0-255 range, so map the rgb values here
    # TODO check whether this mapping can be avoided by generating values already in 0-255 through matplotlib
    #      or maybe potree viewer can also adjust for 0.0-1.0 values
    r *= 255.0
    g *= 255.0
    b *= 255.0
    return r, g, b


def build_color_mapper(series: DataFrame) -> cm.ScalarMappable:
    """
    Build color mapper for parameter value series
    :param series: the series of some parameter value from simulation stream
    :return: the ScalarMappable color mapper
    """
    min_val = series.min()
    max_val = series.max()
    norm = mpl.colors.Normalize(vmin=min_val, vmax=max_val)
    return cm.ScalarMappable(norm=norm, cmap=cm.nipy_spectral)


def las_to_entwine(las_path: str, out_path: str) -> None:
    """
    Converts .las file to format recognizable by potree viewer
    :param las_path:
    :param out_path:
    :return:
    """
    process = subprocess.Popen(('entwine', 'build', '-i', las_path, '-o', out_path, '-t', '4'))
    process.wait()

