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
import sys
import argparse
import logging
import traceback
import importlib


#--------------
# local imports
# -------------

from . import __version__

# ----------------
# Module constants
# ----------------

LOG_CHOICES = ('critical', 'error', 'warn', 'info', 'debug')

# -----------------------
# Module global variables
# -----------------------

log = logging.getLogger()
package = __name__.split(".")[0]

# ----------
# Exceptions
# ----------


# ------------------------
# Module utility functions
# ------------------------

def configure_logging(options):
    if options.verbose:
        level = logging.DEBUG
    elif options.quiet:
        level = logging.ERROR
    else:
        level = logging.INFO
    
    log.setLevel(level)
    # Log formatter
    #fmt = logging.Formatter('%(asctime)s - %(name)s [%(levelname)s] %(message)s')
    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    # create console handler and set level to debug
    if options.console:
        ch = logging.StreamHandler()
        ch.setFormatter(fmt)
        ch.setLevel(logging.DEBUG) # All logging handles to the MAX level
        log.addHandler(ch)
    # Create a file handler suitable for logrotate usage
    if options.log_file:
        #fh = logging.handlers.WatchedFileHandler(options.log_file)
        fh = logging.handlers.TimedRotatingFileHandler(options.log_file, when='midnight', interval=1, backupCount=365)
        fh.setFormatter(fmt)
        fh.setLevel(logging.DEBUG) # All logging handles to the MAX level
        log.addHandler(fh)

    if options.modules:
        modules = options.modules.split(',')
        print(modules)
        for module in modules:
            logging.getLogger(module).setLevel(logging.DEBUG)


def valid_file(path):
    if not os.path.isfile(path):
        raise IOError(f"Not valid or existing file: {path}")
    return path

def valid_dir(path):
    if not os.path.isdir(path):
        raise IOError(f"Not valid or existing directory: {path}")
    return path

           
# -----------------------
# Module global functions
# -----------------------


def create_parser():
    # create the top-level parser
    name = os.path.split(os.path.dirname(sys.argv[0]))[-1]
    parser    = argparse.ArgumentParser(prog=name, description='Location utilities for TESS-W')

    # Global options
    parser.add_argument('--version', action='version', version='{0} {1}'.format(name, __version__))
    parser.add_argument('-x', '--exceptions', action='store_true',  help='print exception traceback when exiting.')
    parser.add_argument('-c', '--console', action='store_true',  help='log to console.')
    parser.add_argument('-l', '--log-file', type=str, default=None, action='store', metavar='<file path>', help='log to file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', action='store_true', help='Verbose logging output.')
    group.add_argument('-q', '--quiet',   action='store_true', help='Quiet logging output.')
    parser.add_argument('-m', '--modules', type=str, default=None, action='store', help='comma separated list of modules to activate debug level upon')


    # --------------------------
    # Create first level parsers
    # --------------------------

    subparser = parser.add_subparsers(dest='command')

    parser_registry  = subparser.add_parser('registry', help='registry commands')
    parser_readings = subparser.add_parser('readings', help='readings commands')
   

    # -----------------------------------------
    # Create second level parsers for 'registry'
    # -----------------------------------------

    subparser = parser_registry.add_subparsers(dest='subcommand')
    scan = subparser.add_parser('scan',  help="Generate cross IDA/tessdb CSV comparison")
   

    # -----------------------------------------
    # Create second level parsers for 'readings'
    # -----------------------------------------

    subparser = parser_readings.add_subparsers(dest='subcommand')
    scan = subparser.add_parser('generate',  help="Generate cross IDA/tessdb CSV comparison")
   

    # ------------------------------------------
    # Create second level parsers for 'zptess'
    # ------------------------------------------

    # subparser = parser_zptess.add_subparsers(dest='subcommand')
    
    # zpt = subparser.add_parser('generate',  help="Generate cross zptess/tessdb CSV comparison")
    # zpt.add_argument('-f', '--file', type=str, required=True, help='Output CSV File')
    # zpex1 = zpt.add_mutually_exclusive_group(required=True)
    # zpex1.add_argument('--common', action='store_true', help='Common MACs')
    # zpex1.add_argument('--zptess', action='store_true', help='MACs in ZPTESS not in TESSDB')
    # zpex1.add_argument('--tessdb', action='store_true', help='MACs in TESSDB not in ZPTESS')

    # zpex1 = zpt.add_mutually_exclusive_group(required=True)
    # zpex1.add_argument('-c', '--current', action='store_true', help='Current ZP')
    # zpex1.add_argument('-i', '--historic', action='store_true', help='Historic ZP entries')


    return parser


# ================ #
# MAIN ENTRY POINT #
# ================ #


def main():
    """
    Utility entry point
    """
    options = argparse.Namespace()
    exit_code = 0
    try:
        options = create_parser().parse_args(sys.argv[1:], namespace=options)
        configure_logging(options)
        log.info(f"============== {__name__} {__version__} ==============")
        command = f"{options.command}"
        subcommand = f"{options.subcommand}"
        try:
            log.debug("loading command from module %s in package %s", command, package)
            command = importlib.import_module(command, package=package)
        except ModuleNotFoundError:  # when debugging module in git source tree ...
            command = f".{options.command}"
            log.debug("retrying loading command from module %s in package %s", command, package)
            command = importlib.import_module(command, package=package)
        getattr(command, subcommand)(options)
    except AttributeError:
            log.critical("[%s] No subcommand was given ", __name__)
            traceback.print_exc()
            exit_code = 1
    except KeyboardInterrupt:
        log.critical("[%s] Interrupted by user ", __name__)
    except Exception as e:
        log.critical("[%s] Fatal error => %s", __name__, str(e))
        traceback.print_exc()
    finally:
        pass
    sys.exit(exit_code)
