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
import argparse
from utils import get_config, get_nii_dir

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)
SKIP_CMD=False

def process_bet(source_file=None, source_suffix=".nii.gz", target_suffix="_bet.nii.gz"):
    BET_FLAGS = get_config().BET_FLAGS

    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))
    log.info(f"{source_file} -> {target_file}")
    cmd = ["bet", source_file.as_posix(), target_file.as_posix(), *BET_FLAGS.split(' ')]
    log.info(f"{' '.join(cmd)}")
    if SKIP_CMD is False:
        subprocess.call(cmd)
    return target_file


def process_reorient(source_file=None, source_suffix=".nii.gz", target_suffix="_reorient.nii.gz"):
    FSLREORIENT2DSTD_FLAGS = get_config().FSLREORIENT2DSTD_FLAGS
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    cmd = ["fslreorient2std", source_file.as_posix(), target_file.as_posix(), *FSLREORIENT2DSTD_FLAGS.split(' ')]
    log.info(f"{' '.join(cmd)}")
    if SKIP_CMD is False:
        subprocess.call(cmd)
    return target_file


def process_registration(source_file=None, source_suffix=".nii.gz", target_suffix="_registered.nii.gz"):
    FLIRT_FLAGS = get_config().FLIRT_FLAGS
    REFERENCE_TEMPLATE = get_config().REFERENCE_TEMPLATE
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    cmd = ["flirt", "-in", source_file.as_posix(), "-out", target_file.as_posix(), "-ref", REFERENCE_TEMPLATE,
           *FLIRT_FLAGS.split(' ')]
    log.info(f"{' '.join(cmd)}")
    if SKIP_CMD is False:
        subprocess.call(cmd)
    return target_file


def process_pipeline(source_file, do_bet=False, do_reorient=False, do_registration=False):

    if do_bet == False:
        log.info("no registration")
        return
    source_file = process_bet(source_file, target_suffix="_bet.nii.gz")
    if source_file.is_file():
        log.info("created: {source_file}")
    else:
        log.info("failed to create {source_file}. Skip to next task")
        return

    if do_reorient == False:
        log.info("no registration")
        return
    source_file = process_reorient(source_file, target_suffix="_reorient.nii.gz")
    if source_file.is_file():
        log.info("created: {source_file}")
    else:
        log.info("failed to create {source_file}. Skip to next task")
        return

    if do_registration == False:
        log.info("no registration")
        return
    source_file = process_registration(source_file, target_suffix="_registered.nii.gz")
    if source_file.is_file():
        log.info("created: {source_file}")
    else:
        log.info("failed to create {source_file}. Skip to next task")
        return

    return


def main(do_bet=False, do_reorient=False, do_registration=False):
    nii_dir = get_nii_dir()

    files = list(Path(nii_dir).glob("Anonymized_-_0*/Head_Demyelination/time_*/*.nii.gz"))
    futures = []
    with ProcessPoolExecutor() as executor:
        for source_file in files:
            log.info(f'working on {source_file}')
            # process_pipeline(source_file)
            futures.append(executor.submit(process_pipeline, source_file, do_bet, do_reorient, do_registration))

    wait(futures)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepare directory for stripping and registration')
    parser.add_argument('--bet', help='perform brain extraction', action='store_false')
    parser.add_argument('--reorient', help='perform reorientation', action='store_false')
    parser.add_argument('--registration', help='perform registration', action='store_false')

    args = parser.parse_args()
    log.info(f"{args}")

    main(do_bet=args.bet, do_reorient=args.reorient, do_registration=args.registration)
    sys.exit(1)
