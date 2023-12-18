# ----------------------------------------------------------------------
# Copyright (c) 2020
#
# See the LICENSE file for details
# see the AUTHORS file for authors
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import os
import re
import csv
import logging
import sqlite3
import functools
import glob
import datetime


# -------------------
# Third party imports
# -------------------

#--------------
# local imports
# -------------

from .utils import remove_duplicates, group_by_name, assert_timestamps, get_tessdb_connection_string, get_tessdb_logfiles_dir, open_database, render_from

# ----------------
# Module constants
# ----------------

SQL_FOO = 'foo.j2'

TOP_LOGFILE = 'tessdb.log-20231215' # Date of migration to TESS4C

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -------------------------
# Module auxiliar functions
# -------------------------

render = functools.partial(render_from, 'tess4c')

RE_REG = r'(\d{4}-\d{2}-\d{2}T\d{2}\:\d{2}\:\d{2}\+\d{4}) \[mqttS#error\] No "calib" keyword sent in registration message=(.+)'
RE_READ = r'(\d{4}-\d{2}-\d{2}T\d{2}\:\d{2}\:\d{2}\+\d{4}) \[mqttS#error\] Validation error in readings payload=(.+)'



EXCLUDED_NAMES = ('stars4C1','Prub4c2','Pru24c','Prueba')

def filter_unwanted_names(a_dict, excluded_names):
	for key in excluded_names:
		del a_dict[key]

def remove_duplicated_registry(a_dict):
    for key, values in a_dict.items():
        indexes_to_delete = list()
        for i, item in enumerate(values):
            if i == 0:
                continue
            if values[i-1]['text'] == values[i]['text']:
                log.warn("%s: Duplicate registry messages for positions %d and %d", key, i-1, i)
                log.debug("%s <=> %s", values[i-1], values[i])
                indexes_to_delete.append(i)
        for i in sorted(indexes_to_delete, reverse=True):
            log.warn("%s: Deleting position %d", key, i)
            del values[i]

# ===================
# Module entry points
# ===================

def scan(options):
    log.info("====================== REGISTRY SCAN ======================")
    database = get_tessdb_connection_string()
    base_dir = get_tessdb_logfiles_dir()
    wildcard = os.path.join(base_dir, 'tessdb.log-????????')
    top_file = os.path.join(base_dir, TOP_LOGFILE)
    total_files = (path for path in sorted(glob.iglob(wildcard)) if path <= top_file)
    register_messages = group_by_name(total_files, RE_REG)
    filter_unwanted_names(register_messages, EXCLUDED_NAMES)
    remove_duplicates(register_messages)
    log.info("====================== REGISTRY SCAN 2 ======================")
    remove_duplicated_registry(register_messages)
