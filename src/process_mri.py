#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Prepares the directories by call dcm2niix to convert dcm to nii in the right folders
"""
__author__ = "Aonghus Lawlor"
__copyright__ = "Copyright 2021, Aonghus Lawlor"
__credits__ = ["Aonghus Lawlor", "Brendan Kelly"]
__license__ = "GPLv3.0"
__version__ = "1.0"
__maintainer__ = "Aonghus Lawlor"
__email__ = "aonghus.lawlor@ucd.ie"
__status__ = "Development"

import sys
from pathlib import Path
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
import logging
from utils import get_config, get_nii_dir

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)


def process_bet(source_file=None, source_suffix=".nii.gz", target_suffix="_bet.nii.gz"):
    BET_FLAGS = get_config().BET_FLAGS

    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))
    cmd = ["bet", source_file.as_posix(), target_file.as_posix(), *BET_FLAGS.split(' ')]
    log.info(f"{' '.join(cmd)}")
    subprocess.call(cmd)
    return target_file


def process_reorient(source_file=None, source_suffix=".nii.gz", target_suffix="_reorient.nii.gz"):
    FSLREORIENT2DSTD_FLAGS = get_config().FSLREORIENT2DSTD_FLAGS
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    cmd = ["fslreorient2std", source_file.as_posix(), target_file.as_posix(), *FSLREORIENT2DSTD_FLAGS.split(' ')]
    log.info(f"{' '.join(cmd)}")
    subprocess.call(cmd)
    return target_file


def process_registration(source_file=None, source_suffix=".nii.gz", target_suffix="_registered.nii.gz"):
    FLIRT_FLAGS = get_config().FLIRT_FLAGS
    REFERENCE_TEMPLATE = get_config().REFERENCE_TEMPLATE
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    cmd = ["flirt", "-in", source_file.as_posix(), "-out", target_file.as_posix(), "-ref", REFERENCE_TEMPLATE,
           *FLIRT_FLAGS.split(' ')]
    log.info(f"{' '.join(cmd)}")
    subprocess.call(cmd)
    return target_file


def process_pipeline(source_file):

    source_file = process_bet(source_file, "_bet.nii.gz")
    source_file = process_reorient(source_file, "_reorient.nii.gz")
    source_file = process_registration(source_file, "_registered.nii.gz")
    return


def main():
    nii_dir = get_nii_dir()

    files = list(Path(nii_dir).glob("Anonymized_-_0*/Head_Demyelination/time_*/*.nii.gz"))
    futures = []
    with ProcessPoolExecutor() as executor:
        for source_file in files:
            log.info('working on', source_file)
            # process_pipeline(source_file)
            futures.append(executor.submit(process_pipeline, source_file))

    wait(futures)
    return


if __name__ == '__main__':
    main()
    sys.exit(1)
