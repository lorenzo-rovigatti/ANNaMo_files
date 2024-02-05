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

Note that `ANNaMo` is implemented as an [oxDNA plugin](https://lorenzo-rovigatti.github.io/oxDNA/input.html#plugins-options), which means that input files should contain the correct `plugin_search_path` values.

### File formats

The configuration file has the [same format](https://lorenzo-rovigatti.github.io/oxDNA/configurations.html) as oxDNA. By contrast, the topology file is unique to ANNaMo. The first line specifies the total number of beads and the total number of strands. The subsequent lines specify the id, type, and connectivity of each bead, two lines per bead. The syntax is the following:

```
ID type number_bonded_beads
ID_bonded_bead1 ID_bonded_bead2
```

The beads are listed on a per-strand basis: an empty line signals that all the beads of a strand have been specified. As an example, here is the topology of a 2-strand system made of 3 beads each:

```
6 2
0 1 1
1
1 2 2
0 2
2 3 1
1

3 5 1
4
4 6 2
3 5
5 7 1
4

```

The bead type is used in the `dHdS_matrix.dat` files to specify the $\Delta H$ and $\Delta S$​ associated to each bead pair. This is done using the following syntax:

```
dH[type_1][type_2] = delta_H
dS[type_1][type_2] = delta_S
```

By default, all unspecified interactions are set to 0. 

As an example, this is the `dHdS_matrix.dat` file from the `examples/DNA_duplexes/3beads/couple10` folder, whose topology file was shown earlier:

```
dH[1][2] = -1.5
dS[1][2] = -6.1
dH[1][5] = 4.766666666666667
dS[1][5] = 6.699999999999999
dH[1][6] = 0.36666666666666664
dS[1][6] = -2.2
dH[1][7] = -18.833333333333332
dS[1][7] = -53.8
dH[2][5] = -0.33333333333333337
dS[2][5] = -6.0
dH[2][6] = -28.233333333333334
dS[2][6] = -73.9
dH[2][7] = -1.3333333333333333
dS[2][7] = -5.9
dH[3][5] = -17.733333333333334
dS[3][5] = -48.6
dH[3][6] = -5.733333333333333
dS[3][6] = -18.2
dH[3][7] = -2.833333333333333
dS[3][7] = -13.0
dH[6][7] = -4.0
dS[6][7] = -13.2
```

where we omitted all the entries equal to zero.

## Example simulations

The `examples` folder contains all the files required to run simulations of the systems showcased in the paper. Each leaf subfolder contains the following files:

* `input` is the oxDNA input file.
* `topology.dat` is the topology file.
* `dHdS_matrix.dat` specifies the interactions between beads in terms of $\Delta H$ and $\Delta S$​​.

Head over to `examples/README.md` and `examples/FFS/README.md` for more details.

## Additional scripts

The `scripts` folder contains additional utility scripts.

### Forward flux sampling (FFS)

The FFS simulations in the paper have been run with the `ffs_flux.py` and `ffs_shoot.py` scripts. Defining $A$ and $B$ as the two metastable states between which the rate should be computed and $\lambda_i$ as the $i$-th interface that separates them,  `ffs_flux.py` is used to obtain an estimate of the flux exiting from $A$, while `ffs_shoot.py` evaluates the probability that $\lambda_i$ is crossed.

Both scripts take als file as input and require the [oxpy](https://lorenzo-rovigatti.github.io/oxDNA/oxpy/index.html) and [numpy](https://numpy.org/) Python packages to be installed. A runnable example containing one of the systems undergoing a toehold-mediated strand displacement process studied in the paper can be found in the `examples/FFS` folder.
