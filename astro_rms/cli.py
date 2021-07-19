#!/usr/bin/env python

from . import version
import sys
import argparse
from astropy import log
from pathlib import Path
import pyaml


def main(args=None):

    prog_name = 'AstroRMS'
    prog_desc = 'Re-packaging of the AstroRMS tool by Matt Mechtley (2011).'

    parser = argparse.ArgumentParser(
            description=f"{prog_name} v{version.version} - {prog_desc}"
            )
    parser.add_argument(
            'sci_file',
            help="Signal map."
            )
    parser.add_argument(
            'wht_file',
            help="Weight map."
            )
    parser.add_argument(
            '-t', '--output_type',
            required=False, default='ivm',
            choices=['ivm', 'rms', 'var'],
            help="Output data type. Default is inverse variance map (ivm).",
            )
    parser.add_argument(
            '-o', '--output',
            required=False, default=None,
            help="Output file. The default is "
                 "{sci_filename}_{output_type}.fits",
            )
    parser.add_argument(
            "-q", "--quiet",
            help="Suppress debug logging messages.",
            action='store_true')
    parser.add_argument(
            '-v', '--version', action='version',
            help='Print the version info and exit.',
            version=version.version
            )

    option = parser.parse_args(args or sys.argv[1:])

    if option.quiet:
        loglevel = 'INFO'
    else:
        loglevel = 'DEBUG'
    log.setLevel(loglevel)

    log.debug(option)

    if option.output is None:
        output = '{}_rms.fits'.format(Path(option.sci_file).stem)
    else:
        output = option.output
    log.info(f"output rms file: {output}")

    from .extern.astroRMS import astroRMS

    stats = astroRMS.create_error_map(
            option.sci_file, option.wht_file, output,
            map_type=option.output_type,
            return_stats=True)

    log.info(f"Summary:\n{pyaml.dump(stats)}")
