# ANNaMo_files

Code and examples for the ANNaMo model.

## The simulation code

ANNaMo simulations are run with [oxDNA](https://github.com/lorenzo-rovigatti/oxDNA). The repository contains a snapshot dated 05/02/2024, which can be compiled with the following commands:

```
cd oxDNA
mkdir build
cd build
cmake .. -DPython=On
make install -j6
make rovigatti tostiguerra -j6
```

At the end of the compilation stage, the `oxDNA` executable will be placed in the `build/bin` folder, and the [oxpy Python bindings](https://lorenzo-rovigatti.github.io/oxDNA/oxpy/index.html) will be installed on the system. Check the [oxDNA docs](https://lorenzo-rovigatti.github.io/oxDNA/) for additional information.

Note that `ANNaMo` is implemented as an [oxDNA plugin](https://lorenzo-rovigatti.github.io/oxDNA/input.html#plugins-options), which means that input files should contain the correct `plugin_search_path`s (see below for more information).

## Example simulations

The `examples` folder contains all the files required to run simulations of the systems showcased in the paper. Each leaf subfolder contains the following files:

* `input` is the oxDNA input file.
* `init_conf.dat` is the initial configuration.
* `topology.dat` is the topology file.
* `dHdS_matrix.dat` specifies the interactions between beads in terms of $\Delta H$ and $\Delta S$.

## Additional scripts

The `scripts` folder contains additional utility scripts.

### Forward flux sampling (FFS)

The FFS simulations in the paper have been run with the `ffs_flux.py` and `ffs_shoot.py` scripts. Defining $A$ and $B$ as the two metastable states between which the rate should be computed and $\lambda_i$ as the $i$-th interface that separates them,  `ffs_flux.py` is used to obtain an estimate of the flux exiting from $A$, while `ffs_shoot.py` evaluates the probability that $\lambda_i$ is crossed.

Both scripts take a [TOML](https://toml.io/en/) file as input and require the [oxpy](https://lorenzo-rovigatti.github.io/oxDNA/oxpy/index.html) and [numpy](https://numpy.org/) Python packages to be installed. A runnable example containing one of the systems undergoing a toehold-mediated strand displacement process studied in the paper can be found in the `examples/FFS` folder.
