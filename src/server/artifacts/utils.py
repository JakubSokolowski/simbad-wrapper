import ntpath
import os
import shutil


def path_leaf(path: str) -> str:
    """
    Returns the leaf of the path:
    /home/some/path -> path
    /home/some/path/file.csv -> file.csv
    :param path:
    :return:
    """
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def compress_artifact(path: str) -> str:
    """
    Compresses artifact (or folder in case of .parquet artifacts) to zip format
    :param path: path to artifact or folder with artifacts
    :return: path to created zip file
    """
    if os.path.isdir(path):
        artifact_dir: str = path
        parent_dir: str = os.path.dirname(path)
        archive_name: str = path_leaf(path)
        archive_path: str = "{}/{}".format(parent_dir, archive_name)
        shutil.make_archive(archive_path, 'zip', artifact_dir)
        return "{}/{}".format(parent_dir, archive_name + '.zip')
    # TODO Quick and dirty method -> refactor to avoid code duplication
    else:
        if path.endswith('.png'):
            return path
        parent_dir: str = os.path.dirname(path)
        archive_name: str = path_leaf(path)
        archive_path = "{}/{}".format(parent_dir, archive_name)
        shutil.make_archive(archive_path, 'zip', parent_dir, path_leaf(path))
        return "{}/{}".format(parent_dir, archive_name + '.zip')


