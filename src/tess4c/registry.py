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

from .utils import group_by_name, assert_timestamps, get_tessdb_connection_string, get_tessdb_logfiles_dir, open_database, render_from

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
    assert_timestamps(register_messages)
    