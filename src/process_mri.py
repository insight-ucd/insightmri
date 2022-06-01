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
import subprocess
import logging
import argparse
import multiprocessing as mp
from utils import get_config, get_nii_dir, get_dir_structure
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
from nipype.interfaces import fsl

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)

log = logging.getLogger(__name__)
SKIP_CMD = False


def process_bet(source_file=None, source_suffix=".nii.gz", target_suffix="_bet.nii.gz"):
    BET_FLAGS = get_config().BET_FLAGS

    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))
    log.info(f"{source_file} -> {target_file}")
    bet_converter = fsl.BET()
    bet_converter.inputs.in_file = source_file
    bet_converter.inputs.out_file = target_file
    bet_converter.inputs.output_type = 'NIFTY_GZ'
    bet_converter.inputs.args = BET_FLAGS
    if not SKIP_CMD:
        log.info(f"{bet_converter.cmdline}")
        bet_converter.run()
    return target_file


def process_reorient(source_file=None, source_suffix=".nii.gz", target_suffix="_reorient.nii.gz"):
    FSLREORIENT2DSTD_FLAGS = get_config().FSLREORIENT2DSTD_FLAGS
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    reorient_converter = fsl.Reorient2Std()
    reorient_converter.inputs.in_file = source_file
    reorient_converter.inputs.args = FSLREORIENT2DSTD_FLAGS
    reorient_converter.inputs.out_file = target_file
    reorient_converter.inputs.output_type = 'NIFTY_GZ'

    if not SKIP_CMD:
        log.info(f"{reorient_converter.cmdline}")
        reorient_converter.run()
    return target_file


def process_registration(source_file=None, source_suffix=".nii.gz", target_suffix="_registered.nii.gz"):
    FLIRT_FLAGS = get_config().FLIRT_FLAGS
    REFERENCE_TEMPLATE = get_config().REFERENCE_TEMPLATE
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    flirt_converter = fsl.FLIRT()
    flirt_converter.inputs.in_file = source_file
    flirt_converter.inputs.args = FLIRT_FLAGS
    flirt_converter.inputs.out_file = target_file
    flirt_converter.inputs.reference = REFERENCE_TEMPLATE
    flirt_converter.inputs.output_type = 'NIFTY_GZ'
    if not SKIP_CMD:
        log.info(f"{flirt_converter.cmdline}")
        flirt_converter.run()
    return target_file


def process_pipeline(source_file, do_bet=False, do_reorient=False, do_registration=False):

    if not do_bet :
        log.info("no registration")
        #return
    else:
        source_file = process_bet(source_file, target_suffix="_bet.nii.gz")
        if source_file.is_file():
            log.info(f"created: {source_file}")
        else:
            log.info(f"failed to create {source_file}. Skip to next task")
            return

    if not do_reorient:
        log.info("no registration")
        #return
    else:
        source_file = process_reorient(source_file, target_suffix="_reorient.nii.gz")
        if source_file.is_file():
            log.info(f"created: {source_file}")
        else:
            log.info(f"failed to create {source_file}. Skip to next task")
            return

    if not do_registration:
        log.info("no registration")
        #return
    else:
        source_file = process_registration(source_file, target_suffix="_registered.nii.gz")
        if source_file.is_file():
            log.info(f"created: {source_file}")
        else:
            log.info(f"failed to create {source_file}. Skip to next task")
            return

    return


def main(do_bet=False, do_reorient=False, do_registration=False, n_workers=0):
    if n_workers == 0:
        n_workers = mp.cpu_count() - 1
    nii_dir = get_nii_dir()

    files = list(Path(nii_dir).glob(get_dir_structure()))
    futures = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        for source_file in files:
            log.info(f'working on {source_file}')
            # process_pipeline(source_file)
            futures.append(executor.submit(process_pipeline, source_file, do_bet, do_reorient, do_registration))

    wait(futures)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepare directory for stripping and registration')
    parser.add_argument('--bet', help='perform brain extraction', action='store_true')
    parser.add_argument('--reorient', help='perform reorientation', action='store_true')
    parser.add_argument('--registration', help='perform registration', action='store_true')
    parser.add_argument('--n_workers', help='number of processes', default=0, type=int)

    args = parser.parse_args()
    log.info(f"{args}")

    main(do_bet=args.bet, do_reorient=args.reorient, do_registration=args.registration, n_workers=args.n_workers)
    sys.exit(1)
