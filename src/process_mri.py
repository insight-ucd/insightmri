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
import fcntl
from utils import get_config, get_nii_dir, get_dir_structure
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed, wait
from nipype.interfaces import fsl
from datetime import datetime

logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)

SKIP_CMD = False


def write_cmd(file, cmd):
    with open(file, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(cmd)
        fcntl.flock(f, fcntl.LOCK_UN)


def process_bet(source_file=None, source_suffix=".nii.gz", target_suffix="_bet.nii.gz", write_to_file=False):
    BET_FLAGS = get_config().BET_FLAGS

    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))
    #log.info(f"BET - {source_file} -> {target_file}")
    flair_names = ['FLAIR', 'flair', 'Flair']

    if any(x in source_file.as_posix() for x in flair_names):
        FLAGS = get_config().FLAIR_BET_FLAGS
    else:
        FLAGS = BET_FLAGS
    bet_converter = fsl.BET()
    bet_converter.inputs.in_file = source_file.resolve()
    bet_converter.inputs.out_file = target_file
    bet_converter.inputs.output_type = 'NIFTI_GZ'
    bet_converter.inputs.args = FLAGS
    if not SKIP_CMD:
        if write_to_file:
            return bet_converter.cmdline
        else:
            log.info(f"{bet_converter.cmdline}")
            bet_converter.run()
    return target_file


def process_reorient(source_file=None, source_suffix=".nii.gz", target_suffix="_reorient.nii.gz", write_to_file=False):
    FSLREORIENT2DSTD_FLAGS = get_config().FSLREORIENT2DSTD_FLAGS
    target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))

    reorient_converter = fsl.Reorient2Std()
    reorient_converter.inputs.in_file = source_file.resolve()
    reorient_converter.inputs.args = FSLREORIENT2DSTD_FLAGS
    reorient_converter.inputs.out_file = target_file
    reorient_converter.inputs.output_type = 'NIFTI_GZ'

    if not SKIP_CMD:
        if write_to_file:
            return reorient_converter.cmdline
        else:
            log.info(f"{reorient_converter.cmdline}")
            reorient_converter.run()
    return target_file


def process_registration(source_file=None, source_suffix=".nii.gz", target_suffix="_registered.nii.gz",
                         write_to_file=False):
    if source_file.as_posix().endswith(source_suffix):
        FLIRT_FLAGS = get_config().FLIRT_FLAGS
        REFERENCE_TEMPLATE = get_config().REFERENCE_TEMPLATE
        target_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, target_suffix))
        mat_file = Path(source_file.parents[0] / source_file.name.replace(source_suffix, ".mat"))

        flirt_converter = fsl.FLIRT()
        flirt_converter.inputs.in_file = source_file
        flirt_converter.inputs.args = FLIRT_FLAGS
        flirt_converter.inputs.out_file = target_file
        flirt_converter.inputs.reference = REFERENCE_TEMPLATE
        flirt_converter.inputs.out_matrix_file = mat_file
        flirt_converter.inputs.output_type = 'NIFTI_GZ'
        if not SKIP_CMD:
            if write_to_file:
                return flirt_converter.cmdline
            else:
                log.info(f"{flirt_converter.cmdline}")
                flirt_converter.run()
        return target_file
    else:
        return None


def process_pipeline(source_file, do_bet=False, do_reorient=False, do_registration=False, script_name=None):
    write_to_file = False
    if script_name is not None:
        write_to_file = True

    if not do_bet:
        log.info("no BET")
        # return
    else:
        ret = process_bet(source_file, target_suffix="_bet.nii.gz", write_to_file=write_to_file)
        if isinstance(ret, Path) and ret.is_file():
            source_file = ret
            log.info(f"created: {source_file}")
        elif isinstance(ret, str):
            write_cmd(script_name, ret+"\n")
            log.info(f"writing command to file")
        else:
            log.info(f"failed to create {ret}. Skip to next task")
            return

    if not do_reorient:
        log.info("no Reorient")
        # return
    else:
        ret = process_reorient(source_file, target_suffix="_reorient.nii.gz", write_to_file=write_to_file)
        if isinstance(ret, Path) and ret.is_file():
            source_file = ret
            log.info(f"created: {source_file}")
        elif isinstance(ret, str):
            write_cmd(script_name, ret+"\n")
            log.info(f"writing command to file")
        else:
            log.info(f"failed to create {source_file}. Skip to next task")
            return

    if not do_registration:
        log.info("no registration")
        # return
    else:
        source_suffix = "_bet.nii.gz"
        ret = process_registration(source_file, source_suffix=source_suffix,
                                   target_suffix="_registered.nii.gz", write_to_file=write_to_file)
        if ret is None:
            log.info(f"File: {source_file} does not match provided suffix {source_suffix}")
        elif isinstance(ret, Path) and ret.is_file():
            source_file = ret
            log.info(f"created: {source_file}")
        elif isinstance(ret, str):
            write_cmd(script_name, ret+"\n")
        else:
            log.info(f"failed to create {source_file}. Skip to next task")
            return

    return


def main(do_bet=False, do_reorient=False, do_registration=False, do_script=False, n_workers=0):
    if n_workers == 0:
        n_workers = mp.cpu_count() - 1
    nii_dir = get_nii_dir()
    dir_structure = get_dir_structure().replace(' ', '_')
    script_name = None
    if do_script:
        script_prefix = "script"
        script_suffix = "_conversion"
        if do_bet:
            script_suffix = "_bet" + script_suffix
        if do_reorient:
            script_suffix = "_reorient" + script_suffix
        if do_registration:
            script_suffix = "_registration" + script_suffix
        script_suffix = f"{script_suffix}_{datetime.now().strftime('%d_%m_%H_%M')}.sh"
        script_name = script_prefix + script_suffix
        script_name = f"{nii_dir}/{script_name}"
        with open(script_name, "x") as f:
            log.debug(f"created script : {script_name}")
            pass
    files = list(Path(nii_dir).glob(dir_structure + '/*.nii.gz'))
    log.debug(f"original files :  {len(files)}")
    files = [file for file in files if "ROI" not in file.as_posix() and "EQ" not in file.as_posix()]
    log.debug(f"removing overlay files : {len(files)}")
    futures = []
    with ProcessPoolExecutor(max_workers=n_workers) as executor:
        for source_file in files:
            log.info(f'working on {source_file}')
            # process_pipeline(source_file)
            futures.append(executor.submit(process_pipeline, source_file, do_bet, do_reorient, do_registration,
                                           script_name))

    wait(futures)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepare directory for stripping and registration')
    parser.add_argument('--bet', help='perform brain extraction', action='store_true')
    parser.add_argument('--reorient', help='perform reorientation', action='store_true')
    parser.add_argument('--registration', help='perform registration', action='store_true')
    parser.add_argument('--n_workers', help='number of processes', default=0, type=int)
    parser.add_argument('--script', help="generate conversion script", action='store_true')

    args = parser.parse_args()
    log.info(f"{args}")

    main(do_bet=args.bet, do_reorient=args.reorient, do_registration=args.registration, do_script=args.script,
         n_workers=args.n_workers)
    sys.exit(1)
