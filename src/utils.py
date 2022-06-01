#/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Set of helper functions to prepare the folders
"""
__author__ = "Aonghus Lawlor"
__copyright__ = "Copyright 2021, Aonghus Lawlor"
__credits__ = ["Aonghus Lawlor", "Brendan Kelly"]
__license__ = "GPLv3.0"
__version__ = "1.0"
__maintainer__ = "Aonghus Lawlor"
__email__ = "aonghus.lawlor@ucd.ie"
__status__ = "Development"


import os
import yaml
import logging
from nipype.interfaces.dcm2nii import Dcm2niix
from munch import munchify
from pathlib import Path
from rescale_dicom import rescale_dicom, clean_replace_dir


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)


CONFIG = None


def get_source_dir():
    source = get_config().SOURCE_DIR
    return source


def get_dir_structure():
    return get_config().DIR_STRUCTURE


def get_nii_dir():
    source = get_config().SOURCE_DIR
    return f"/tmp/{source}_nii"


def get_replace_dir():
    source = get_config().SOURCE_DIR
    return f"/tmp/{source}_replace"


def get_registration_dir():
    source = get_config().SOURCE_DIR
    return f"/tmp/{source}_registration"


def get_brainextraction_dir():
    source = get_config().SOURCE_DIR
    return f"/tmp/{source}_brainextraction"


def initialise(clean_old=False):
    """
    prepare the nii files
    :return:
    """
    source_dir = Path(get_source_dir())
    dir_structure = get_config().DIR_STRUCTURE
    nii_dir = Path(get_nii_dir())
    replace_dir = Path(get_replace_dir())
    DCM2NIIX_FLAGS = get_config().DCM2NIIX_FLAGS

    nii_dir.mkdir(parents=True, exist_ok=True)
    replace_dir.mkdir(parents=True, exist_ok=True)

    if clean_old:
        log.info("cleaning old files")
        files = filter(Path.is_file, nii_dir.glob("**/*"))
        r = list(map(lambda x: x.unlink(), files))
        print(r)

    dirs = list(source_dir.glob(dir_structure))

    for s_dir in dirs:
        t_dir = Path(s_dir.as_posix().replace(source_dir.as_posix(), nii_dir.as_posix(), 1))
        t_dir = Path(t_dir.as_posix().replace(' ', '_'))
        t_dir.mkdir(parents=True, exist_ok=True)

        r_dir = Path(s_dir.as_posix().replace(source_dir.as_posix(), replace_dir.as_posix(), 1))
        r_dir = Path(r_dir.as_posix().replace(' ', '_'))
        r_dir.mkdir(parents=True, exist_ok=True)

        input_dir = rescale_dicom(s_dir, r_dir)

        dcm_converter = Dcm2niix()
        dcm_converter.inputs.source_dir = input_dir
        dcm_converter.inputs.args = DCM2NIIX_FLAGS
        dcm_converter.inputs.output_dir = t_dir
        log.info(f"DCM2NIIX version : {dcm_converter.version}")
        log.info(f"Converting [{s_dir}] => [{t_dir}]")
        log.info(f"Interface cmd : {dcm_converter.cmdline}")
        dcm_converter.run()
        clean_replace_dir(input_dir)
    return


def get_config():
    global CONFIG
    if CONFIG is None:
        root = Path(os.path.dirname(os.path.abspath(__file__)))
        try:
            with open(root / "../config.yml", 'r') as f:
                log.info(f"reading config from {f.name}")
                c = yaml.safe_load(f)
                CONFIG = munchify(c)
        except:
            pass
    else:
        log.info('config already loaded')
    return CONFIG
