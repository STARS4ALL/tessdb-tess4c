# -*- coding: utf-8 -*-

# TESS UTILITY TO PERFORM SOME MAINTENANCE COMMANDS

# ----------------------------------------------------------------------
# Copyright (c) 2014 Rafael Gonzalez.
#
# See the LICENSE file for details
# ----------------------------------------------------------------------

#--------------------
# System wide imports
# -------------------

import csv
import os
import re
import datetime
import logging
import collections

# ---------------------
# Third party libraries
# ---------------------

import decouple
import jinja2

#--------------
# local imports
# -------------

# ----------------
# Module constants
# ----------------

TSTAMP_FORMAT = '%Y-%m-%dT%H:%M:%S%z'

# ----------------
# package constants
# ----------------

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger(__name__)

# -----------------------
# Module global functions
# -----------------------

def get_tessdb_connection_string():
   return decouple.config('TESSDB_URL')

def get_tessdb_logfiles_dir():
    return decouple.config('TESSDB_LOGFILES_DIR')


def _scan_file(path, reg_expression):
    '''Used below'''
    regexp = re.compile(reg_expression)
    log.info("Scanning %s", path)
    item_info = list()
    with open(path) as fd:
        for i, line in enumerate(fd):
            matchobj = regexp.search(line.strip())
            if matchobj:
                # Logfile oputpus in local time
                tstamp = datetime.datetime.strptime(matchobj.group(1), TSTAMP_FORMAT)
                # From Local time to UTC
                tstamp = (tstamp - tstamp.utcoffset()).replace(tzinfo=datetime.timezone.utc)
                text = matchobj.group(2)
                metadata = eval(text)
                metadata['text'] = text
                metadata['tstamp'] = tstamp
                metadata['line'] = i
                metadata['file'] = os.path.basename(path)
                item_info.append(metadata)
    return item_info


def group_by_name(file_sequence, reg_expression):
    result = list()
    for i, path in enumerate(file_sequence, 1):
        metadata = _scan_file(path, reg_expression)
        result.extend(metadata)
    # Classyfy by name
    by_name_info = collections.defaultdict(list)
    for item in result:
        by_name_info[item['name']].append(item) 
    return by_name_info

def assert_timestamps(a_dict):
    for key, values in a_dict.items():
        log.info("CHECKING %s:timestamps in %d values", key, len(values))
        for i, item in enumerate(values):
            if i == 0:
                continue
            assert values[i-1]['tstamp'] <= values[i]['tstamp']
            if values[i-1]['tstamp'] == values[i]['tstamp']:
                log.warn("%s: Duplicate timestamp %s for positions %d and %d", key, item['tstamp'], i-1, i)
                log.debug("%s <=> %s", values[i-1], values[i])

# ================    
# JINJA2 Rendering
# ================

def render_from(package, template, context):
    return jinja2.Environment(
        loader=jinja2.PackageLoader(package, package_path='templates')
    ).get_template(template).render(context)


# ========================    
# CSV reading and Writting
# ========================

def write_csv(sequence, header, path, delimiter=';'):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=header, delimiter=delimiter)
        writer.writeheader()
        for row in sequence:
            writer.writerow(row)
    #log.info("generated CSV file: %s", path)

def read_csv(path, delimiter=';'):
    with open(path, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=delimiter)
        sequence = [row for row in reader]
        return sequence

# ==============
# DATABASE STUFF
# ==============

def open_database(path):
    if not os.path.exists(path):
        raise IOError("No SQLite3 Database file found in {0}. Exiting ...".format(path))
    return sqlite3.connect(path)
 
