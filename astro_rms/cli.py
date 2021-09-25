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
    parser.add_argument(
            '-r', '--region_file', default=None,
            help='An optional DS9 region file to specify the region slices for'
                 ' computing the noise autocorrelations.'
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

    # parse region file if specified

    if option.region_file is not None:
        log.info(f'load regions from {option.region_file}')
        from .region_slices import load_region_slices
        region_slices = load_region_slices(
            option.region_file,
            sci_file=option.sci_file,
            region_file_fmt='ds9')
        if not region_slices:
            raise RuntimeError("No valid region slices found in region file.")
    else:
        region_slices = None
    from .extern.astroRMS import astroRMS

    stats = astroRMS.create_error_map(
            option.sci_file, option.wht_file, output,
            map_type=option.output_type,
            region_slices=region_slices,
            return_stats=True)

    log.info(f"Summary:\n{pyaml.dump(stats)}")
