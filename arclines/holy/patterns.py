""" Module for finding patterns in arc line spectra
"""
from __future__ import (print_function, absolute_import, division, unicode_literals)


import numpy as np
import pdb


def match_quad_to_list(spec_lines, line_list, wv_guess, dwv_guess,
                  tol=2., dwv_uncertainty=0.2):
    """
    Parameters
    ----------
    spec_lines : ndarray
      pixel space
    line_list
    tol

    Returns
    -------
    possible_matches : list
      list of indices of matching quads

    """
    # Setup spec
    npix = spec_lines[-1]-spec_lines[0]
    spec_values = (spec_lines[1:-1]-spec_lines[0])/(
        spec_lines[-1]-spec_lines[0])
    ftol = tol/npix
    #
    possible_start = np.where((line_list > wv_guess[0]) & (line_list < wv_guess[1]))[0]
    possible_matches = []
    for start in possible_start:
        #print("Trying {:g}".format(line_list[start]))
        # Find possible ends
        possible_ends = np.where( (line_list > line_list[start] + npix*dwv_guess*(1-dwv_uncertainty)) &
                                     (line_list < line_list[start] + npix*dwv_guess*(1+dwv_uncertainty)))[0]
        # Loop on ends
        for end in possible_ends:
            values = (line_list[start+1:end]-line_list[start]) / (
                line_list[end]-line_list[start])
            # Test
            diff0 = np.abs(values-spec_values[0])
            tst0 = diff0 < ftol
            diff1 = np.abs(values-spec_values[1])
            tst1 = diff1 < ftol
            #if np.abs(line_list[start]-6097.8) < 0.2:
            #    debugger.set_trace()
            if np.any(tst0) & np.any(tst1):
                i0 = np.argmin(diff0)
                i1 = np.argmin(diff1)
                #if np.sum(tst0) > 1:
                #    pdb.set_trace()
                #possible_matches.append([start, start+1+np.where(tst0)[0][0],
                #                         start+1+np.where(tst1)[0][0], end])
                possible_matches.append([start, start+1+i0, start+1+i1, end])
    # Return
    return possible_matches


def score_quad_matches(fidx):
    """  Grades quad_match results
    Parameters
    ----------
    fidx

    Returns
    -------
    scores : list

    """
    # Loop on indices
    scores = []
    for key in fidx.keys():
        if len(fidx[key]['matches']) == 0:
            scores.append('None')
            continue
        matches = np.array(fidx[key]['matches'])
        nmatch = matches.size
        uni, counts = np.unique(matches, return_counts=True)
        nuni = len(uni)
        max_counts = max(counts)
        # Score
        if (nuni==1) & (nmatch >= 4):
            scores.append('Perf')
        elif nmatch == 0:
            scores.append('None')
        elif (max_counts == 4) & (nmatch == 5):
            scores.append('Good')
        elif (max_counts/nmatch >= 2./3) & (nmatch >= 6):
            scores.append('Good')
        elif (nuni == 1) & (nmatch == 3):
            scores.append('Good')
        elif (max_counts == 3) & (nmatch == 4):
            scores.append('OK')
        elif (nuni == 1) & (nmatch == 2):
            scores.append('Risk')
        else:
            scores.append('Amb')
    # Return
    return scores
