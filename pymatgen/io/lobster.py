# coding: utf-8
# Copyright (c) Pymatgen Development Team.
# Distributed under the terms of the MIT License

from __future__ import division, unicode_literals

import re
import numpy as np

from monty.io import zopen
from pymatgen.electronic_structure.core import Spin

"""
Module for reading Lobster output files. For more information
on LOBSTER see www.cohp.de.
"""

__author__ = "Marco Esters"
__copyright__ = "Copyright 2017, The Materials Project"
__version__ = "0.1"
__maintainer__ = "Marco Esters"
__email__ = "esters@uoregon.edu"
__date__ = "Nov 30, 2017"


class Cohpcar(object):
    """
    Class to read COHPCAR/COOPCAR files generated by LOBSTER.

    Args:
        are_coops: Determines if the file is a list of COHPs or COOPs.
          Default is False for COHPs.

        filename: Name of the COHPCAR file. If it is None, the default
          file name will be chosen, depending on the value of are_coops.


    .. attribute: cohp_data

         Dict that contains the COHP data of the form:
           {bond: {"COHP": {Spin.up: cohps, Spin.down:cohps},
                   "ICOHP": {Spin.up: icohps, Spin.down: icohps},
                   "length": bond length}
         Also contains an entry for the average, which does not have
         a "length" key.

    .. attribute: efermi

         The Fermi energy in eV.

    .. attribute: energies

         Sequence of energies in eV. Note that LOBSTER shifts the energies
         so that the Fermi energy is at zero.

    .. attribute: is_spin_polarized

         Boolean to indicate if the calculation is spin polarized.
    """
    def __init__(self, are_coops=False, filename=None):
        self.are_coops = are_coops
        if filename is None:
            filename = "COOPCAR.lobster" if are_coops \
                        else "COHPCAR.lobster"

        with zopen(filename, "rt") as f:
            contents = f.read().split("\n")

        # The parameters line is the second line in a COHPCAR file. It
        # contains all parameters that are needed to map the file.
        parameters = contents[1].split()
        # Subtract 1 to skip the average
        num_bonds = int(parameters[0]) - 1
        self.efermi = float(parameters[-1])
        if int(parameters[1]) == 2:
            spins = [Spin.up, Spin.down]
            self.is_spin_polarized = True
        else:
            spins = [Spin.up]
            self.is_spin_polarized = False

        # The COHP data start in row num_bonds + 3
        data = np.array([np.array(row.split(), dtype=float)
                         for row in contents[num_bonds+3:]]).transpose()
        self.energies = data[0]

        cohp_data = {"average": {"COHP": {spin: data[1+2*s*(num_bonds+1)]
                                          for s, spin in enumerate(spins)},
                                 "ICOHP": {spin: data[2+2*s*(num_bonds+1)]
                                           for s, spin in enumerate(spins)}}}
        for bond in range(num_bonds):
            label, length, sites = self._get_bond_data(contents[3+bond])
            cohp = {spin: data[2*(bond+s*(num_bonds+1))+3]
                    for s, spin in enumerate(spins)}
            icohp = {spin: data[2*(bond+s*(num_bonds+1))+4]
                     for s, spin in enumerate(spins)}
            cohp_data[label] = {"COHP": cohp, "ICOHP": icohp,
                                "length": length,
                                "sites": sites}
        self.cohp_data = cohp_data

    @staticmethod
    def _get_bond_data(line):
        """
        Subroutine to extract bond label, site indices, and length from
        a LOBSTER header line. The site indices are zero-based, so they
        can be easily used with a Structure object.

        Example header line: No.4:Fe1->Fe9(2.4524893531900283)

        Args:
            line: line in the COHPCAR header describing the bond.

        Returns:
            The bond label, the bond length and a tuple of the site
            indices.
        """

        line = line.split("(")
        length = float(line[-1][:-1])
        # Replacing "->" with ":" makes splitting easier
        sites = line[0].replace("->", ":").split(":")[1:3]
        site_indices = tuple(int(re.split("\D+", site)[1]) - 1
                             for site in sites)
        species = tuple(re.split("\d+", site)[0] for site in sites)
        label = "%s%d-%s%d" % (species[0], site_indices[0] + 1,
                               species[1], site_indices[1] + 1)
        return label, length, site_indices


class Icohplist(object):
    """
    Class to read ICOHPLIST/ICOOPLIST files generated by LOBSTER.

    Args:
        are_coops: Determines if the file is a list of ICOHPs or ICOOPs.
          Defaults to False for ICOHPs.

        filename: Name of the ICOHPLIST file. If it is None, the default
          file name will be chosen, depending on the value of are_coops.


    .. attribute: are_coops
         Boolean to indicate if the populations are COOPs or COHPs.

    .. attribute: is_spin_polarized

         Boolean to indicate if the calculation is spin polarized.

    .. attribute: icohplist

         Dict containing the listfile data of the form:
           {bond: "length": bond length,
                  "number_of_bonds": number of bonds
                  "icohp": {Spin.up: ICOHP(Ef) spin up, Spin.down: ...}}
    """
    def __init__(self, are_coops=False, filename=None):
        self.are_coops = are_coops
        if filename is None:
            filename = "ICOOPLIST.lobster" if are_coops \
                        else "ICOHPLIST.lobster"

        # LOBSTER list files have an extra trailing blank line
        # and we don't need the header.
        with zopen(filename) as f:
            data = f.read().split("\n")[1:-1]

        # If the calculation is spin polarized, the line in the middle
        # of the file will be another header line.
        if "distance" in data[len(data)//2]:
            num_bonds = len(data)//2
            self.is_spin_polarized = True
        else:
            num_bonds = len(data)
            self.is_spin_polarized = False

        icohplist = {}
        for bond in range(num_bonds):
            line = data[bond].split()
            label = "%s-%s" % (line[1], line[2])
            length = float(line[3])
            icohp = float(line[4])
            num = int(line[5])
            icohplist[label] = {"length": length, "number_of_bonds": num,
                                "icohp": {Spin.up: icohp}}
            if self.is_spin_polarized:
                icohp = float(data[bond+num_bonds+1].split()[4])
                icohplist[label]["icohp"][Spin.down] = icohp

        self.icohplist = icohplist
