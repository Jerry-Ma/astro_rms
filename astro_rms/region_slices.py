#!/usr/bin/env python


import functools
from regions import (Regions, SkyRegion)
from astropy import log


@functools.lru_cache(maxsize=64)
def _get_wcs_from_fits(filepath):
    from astropy.io import fits
    from astropy.wcs import WCS

    # convert the content to a set of slices
    # this makes use the wcs of sci file
    with fits.open(filepath, mmap=True) as hdulist:
        for hdu in hdulist:
            if 'CTYPE1' in hdu.header:
                w = WCS(hdu.header)
                return w
    return None


def _region_to_region_slice(region, data_shape=None, trim=True):
    bbox = region.bounding_box
    if data_shape is not None:
        slices_large, _ = bbox.get_overlap_slices(shape=data_shape)
        # note the slices are in (y, x) order
        # but astroRMS requires them in (x, y)
        x_slice, y_slice = (slices_large[1], slices_large[0])
    # no bound check is done
    else:
        x_slice, y_slice = (
            slice(bbox.ixmin, bbox.ixmax),
            slice(bbox.iymin, bbox.iymax),
            )
    return (_trim_slice(x_slice), _trim_slice(y_slice))


def _trim_slice(s):
    def _trim_power_of_2(i):
        v = 1 << (i - 1).bit_length()
        if v > i:
            v = v // 2
        return v

    def _trim_to_factor(i, factor):
        if i % factor > 0:
            i = (i // factor) * factor
        return i

    return slice(s.start, s.start + _trim_to_factor(s.stop - s.start, 4))


def load_region_slices(
        region_file, sci_file=None,
        region_file_fmt='ds9',
        ):
    """Return the region slices from a region file."""

    regions = Regions.read(region_file, format=region_file_fmt)

    # this is expected by astroRMS to be a list of tuples
    region_slices = list()

    if sci_file is not None:
        w = _get_wcs_from_fits(sci_file)
    else:
        w = None
    for r in regions:
        if isinstance(r, SkyRegion):
            if w is None:
                raise ValueError(
                    "An associated FITS file (or WCS header) "
                    "is required to interpret sky regions.")
            r_pix = r.to_pixel(w)
            r_str = f"{r.__class__.__name__}({r.center.to_string('hmsdms')})"
        else:
            r_pix = r
            r_str = (f'{r.__class__.__name__}'
                     f'({r.center.x:.2f}, {r.center.y:.2f})')
        region_slice = _region_to_region_slice(
            r_pix, data_shape=None if w is None else w.array_shape)
        log.info(
            f"add {r_str} -> "
            f"{{}}".format(
                '[{:d}:{:d},{:d}:{:d}] ({:d}, {:d})'.format(
                    region_slice[1].start, region_slice[1].stop,
                    region_slice[0].start, region_slice[0].stop,
                    region_slice[1].stop - region_slice[1].start,
                    region_slice[0].stop - region_slice[0].start,
                )))
        if region_slice is not None:
            region_slices.append(region_slice)
    return region_slices
