import os.path
from pathlib import Path

CONSTANTS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_PATH = str(Path(CONSTANTS_DIR).parents[1])
CLI_PATH = ROOT_PATH + '/bin/simbad-cli'
OUT_PATH = ROOT_PATH + '/output'
