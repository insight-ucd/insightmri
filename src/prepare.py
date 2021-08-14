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

import logging
from utils import initialise
import argparse


logging.basicConfig(format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.DEBUG)
log = logging.getLogger(__name__)


def main(clean_old=False):
    initialise(clean_old=clean_old)
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='prepare directory for stripping and registration')
    parser.add_argument('-c', help='clean out the old files', action='store_true')

    args = parser.parse_args()
    log.info(f"{args} {args.c}")
    main(clean_old=args.c)
