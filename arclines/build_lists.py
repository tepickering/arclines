""" Module for building arcline lists
"""
from __future__ import (print_function, absolute_import, division, unicode_literals)

import numpy as np
import os
import pdb

from collections import OrderedDict

from astropy.table import Table, vstack

from arclines import io as arcl_io
from arclines import load_source
from arclines import defs

import arclines # For path
llist_path = arclines.__path__[0]+'/data/lists/'

def init_line_list():
    """ Initialize a Table for a linelist
    Rigidly enforces table column formats
    Strings are the most annoying

    Returns
    -------
    init_tbl : Table
      One dummy row
    """
    # Get str lengths from defs
    len_line = defs.str_len()['ion']
    len_src = defs.str_len()['Source']
    # Load sources to check
    sources = arcl_io.load_source_table()
    src_files = sources['File'].data
    if src_files.dtype.itemsize > len_src:
        raise ValueError("Sources now exceeds table.  Should fix source name")
    dummy_src = str('#')*len_src
    # Arc Line name
    dummy_line = str('#')*len_line
    #

    # Dict for Table
    idict = OrderedDict()
    idict['ion'] = dummy_line
    idict['wave'] = 0.
    idict['NIST'] = 0
    idict['Instr'] = 0  # Flag for instrument
    idict['amplitude'] = 0
    idict['Source'] = dummy_src

    # Table
    tkeys = idict.keys()
    lst = [[idict[tkey]] for tkey in tkeys]
    init_tbl = Table(lst, names=tkeys)

    # Return
    return init_tbl


def add_instr_source(line_tbl, instr, source_file):
    """
    Parameters
    ----------
    tbl
    instr
    source_file

    Returns
    -------
    Modified in place

    """
    str_len_dict = defs.str_len()
    # Add instrument flag
    line_tbl['Instr'] = defs.instruments()[instr]
    # Add source
    source = np.array([source_file]*len(line_tbl),
                      dtype='S{:d}'.format(str_len_dict['Source']))
    line_tbl['Source'] = source


def create_line_list(line_tbl, source_file, instr, outfile,
                     unknown=False, ions=None):
    """
    Parameters
    ----------
    line_tbl
    source_file : str
    instr : str
      Converted to a flag
    outfile

    """
    # Init -- Mainly to insure formatting
    ini_tbl = init_line_list()
    # Add columns (in place)
    add_instr_source(line_tbl, instr, source_file)
    # Stack
    new_tbl = vstack([ini_tbl, line_tbl], join_type='exact')
    # Cut off first line
    cut_tbl = new_tbl[1:]

    # Unknown list??
    if unknown:
        if ions is None:
            raise IOError("Must provide list of possible ions if unknown")
        line_dict = defs.lines()
        line_flag = 0
        for uion in ions:
            line_flag += line_dict[uion]
        cut_tbl['line_flag'] = line_flag

    # Write
    arcl_io.write_line_list(cut_tbl, outfile)


def update_line_list(new_lines, source_file, instr, line_file,
                     tol_wave=0.1, NIST_tol=0.0001, write=False):
    """ Update/add to lines in line list as applicable
    Not for use on UNKNWN lines

    Parameters
    ----------
    line_tbl
    source_file : str
    instr : str
      Converted to a flag
    tol_wave : float, optional
      Matching tolerance in wavelength
      Anything closer than this, even if real, is trouble
    outfile

    """
    # Load
    line_list = arcl_io.load_line_list(line_file)
    # Add columns (in place)
    add_instr_source(new_lines, instr, source_file)

    # Loop to my loop
    updated = False
    for line in new_lines:
        # NIST
        if line['NIST'] != 1:
            print("Not ready for this")
            pdb.set_trace()
        # Search for wavelength match within tolerance
        mtch_wave = np.where(np.abs(line_list['wave']-line['wave']) < tol_wave)[0]
        if len(mtch_wave) == 0:
            if write is False:
                print("Would add the following line to {:s}".format(line_file))
                print(line)
            line_list = vstack([line_list, line]) # Insures columns are matched
            updated = True
        elif len(mtch_wave) == 1:
            idx = mtch_wave[0]
            if np.abs(line_list['wave'][idx]-line['wave']) > NIST_tol:
                print("Bad match for a NIST line")
                print(line)
                print(line_list[idx])
                pdb.set_trace()
            else:  # Check instrument
                if (line_list['Instr'][idx] % (2*line['Instr'])) >= line['Instr']:
                    pass
                else:
                    line_list['Instr'][idx] += line['Instr']
                    if write is False:
                        print("Would update instrument in this line:")
                        print(line_list[idx])
                    updated = True
    # Sort
    line_list.sort('wave')
    # Write
    if write and updated:
        arcl_io.write_line_list(line_list, line_file)


def master_build(write=False, plots=True):
    """ Master loop to build the line lists

    Parameters
    ----------
    check_only : bool, optional
      Only check to see what would be created, i.e. do not execute
    plots : bool, optional
      Generate plots, if write=True too
    """
    # Load sources
    sources = arcl_io.load_source_table()

    # Loop on sources
    for source in sources:
        # Load line table
        ID_lines, U_lines = load_source.load(source['File'], source['Format'], plot=plots)
        # Loop on ID ions
        uions = np.unique(ID_lines['ion'].data)
        for ion in uions:
            # Parse
            idx = ID_lines['ion'] == ion
            sub_tbl = ID_lines[idx]
            # Generate?
            ion_file = llist_path+'{:s}_lines.dat'.format(ion)
            if not os.path.isfile(ion_file):
                if not write:
                    print("Would generate line list:\n   {:s}".format(ion_file))
                else:
                    print("Generating line list:\n   {:s}".format(ion_file))
                    create_line_list(sub_tbl, source['File'],
                                 source['Instr'], ion_file)
            else:
                update_line_list(sub_tbl, source['File'],
                                 source['Instr'], ion_file, write=write)
        # UNKNWN lines
        if U_lines is None:
            continue
        unk_file = llist_path+'UNKNWN_lines.dat'
        # Vette against 'complete' NIST
        if not os.path.isfile(unk_file):
            print("Generating line list:\n   {:s}".format(unk_file))
            create_line_list(U_lines, source['File'], source['Instr'],
                             unk_file, unknown=True, ions=uions)



