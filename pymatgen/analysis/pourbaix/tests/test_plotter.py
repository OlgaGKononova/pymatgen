# coding: utf-8
# Copyright (c) Pymatgen Development Team.
# Distributed under the terms of the MIT License.

from __future__ import unicode_literals

import unittest
import os

from pymatgen.analysis.pourbaix.maker import PourbaixDiagram
from pymatgen.analysis.pourbaix.entry import PourbaixEntryIO

try:
    from pymatgen.analysis.pourbaix.plotter import PourbaixPlotter
    from pymatgen.analysis.pourbaix.analyzer import PourbaixAnalyzer
except ImportError:
    PourbaixAnalyzer = None

test_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'test_files')

@unittest.skipIf(PourbaixAnalyzer is None, "ImportError while importing PourbaixAnalyzer")
class TestPourbaixPlotter(unittest.TestCase):

    def setUp(self):
        module_dir = os.path.dirname(os.path.abspath(__file__))
        (elements, entries) = PourbaixEntryIO.from_csv(os.path.join(module_dir,
                                                    "test_entries.csv"))
        self.num_simplices = {"Zn(s)": 7, "ZnO2(s)": 7, "Zn[2+]": 4, "ZnO2[2-]": 4, "ZnHO2[-]": 4}
        self.e_above_hull_test = {"ZnHO[+]": 0.0693, "ZnO(aq)": 0.0624}
        self.decomp_test = {"ZnHO[+]": {"ZnO(s)": 0.5, "Zn[2+]": 0.5}, "ZnO(aq)": {"ZnO(s)": 1.0}}
        self.pd = PourbaixDiagram(entries)
        self.plotter = PourbaixPlotter(self.pd)

    def test_plot_pourbaix(self):
        plt = self.plotter.get_pourbaix_plot(limits=[[-2, 14], [-3, 3]])

    def test_get_entry_stability(self):
        entry = self.pd.all_entries[0]
        plt = self.plotter.plot_entry_stability(entry, limits=[[-2, 14], [-3, 3]])

if __name__ == '__main__':
    unittest.main()
