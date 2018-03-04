# [HamSCI] Power Density Maps

This repository contains code to generate power density maps. There are two main
scripts: `power_density_map.py` and `power_density_map_with_pop.py`. The first
script plots the power density without using population density to mask land
versus water. The second script does utilize masking in order to distinguish
from land and water.

The `data` directory contains all the 3rd-party files used along with references
to where they were acquired. The `input` directory contains internal data that
is used to generate the output plots. The `output` directory is where the
resulting plots from the scripts are saved.
