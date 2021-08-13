#!/usr/bin/env python
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
from munch import munchify
from pathlib import Path
import subprocess

CONFIG = None

def get_source_dir():
    source = get_config().SOURCE_DIR
    return source

def get_nii_dir():
    source = get_config().SOURCE_DIR
    return f"{source}_nii"


def get_registration_dir():
    source = get_config().SOURCE_DIR
    return f"{source}_registration"


def get_brainextraction_dir():
    source = get_config().SOURCE_DIR
    return f"{source}_brainextraction"


def initialise(clean_old=False):
    """
    prepare the nii files
    :return:
    """
    source_dir = Path(get_source_dir())
    #registration_dir = get_registration_dir()
    #brainextraction_dir = get_brainextraction_dir()
    nii_dir = Path(get_nii_dir())
    DCM2NIIX_FLAGS = get_config().DCM2NIIX_FLAGS

    #Path(registration_dir).mkdir(parents=True, exist_ok=True)
    #Path(brainextraction_dir).mkdir(parents=True, exist_ok=True)
    nii_dir.mkdir(parents=True, exist_ok=True)

    if clean_old == True:
        print("cleaning old files")
        files = filter(Path.is_file, nii_dir.glob("**/*"))
        r = list(map(lambda x: x.unlink(), files))
        print(r)


    dirs = list(source_dir.glob("*/Head Demyelination/time_*"))

    for s_dir in dirs:
        t_dir = Path(s_dir.as_posix().replace(source_dir.as_posix(), nii_dir.as_posix(), 1))       # should be a better way to do this...
        t_dir = Path(t_dir.as_posix().replace(' ', '_'))
        t_dir.mkdir(parents=True, exist_ok=True)
        cmd = ["dcm2niix", *DCM2NIIX_FLAGS.split(' '), "-o", t_dir.as_posix(), s_dir.as_posix()]
        print(s_dir, t_dir, " ".join(cmd))
        subprocess.call(cmd)
    return

def get_config():
    global CONFIG
    if CONFIG == None:
        root = Path(os.path.dirname(os.path.abspath(__file__)))
        try:
            with open(root / "../config.yml", 'r') as f:
                c = yaml.safe_load(f)
                CONFIG = munchify(c)
        except:
            pass
    else:
        print('config already loaded')
    return CONFIG