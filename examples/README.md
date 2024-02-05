# ANNaMo Examples

This folder contains all the files required to simulate the systems investigated in the paper.

## Instructions for all folders but `FFS`

Head to a leaf folder. You will first have to generate an initial configuration by using oxDNA's `confGenerator`, which takes an input file and a box size (in units of the bead diameter $\sigma$) as arguments, like this:

```
PATH/TO/OXDNA/build/bin/confGenerator input 100
```

A simulation can then be run by using the `oxDNA` executable, as follows:

```
PATH/TO/OXDNA/build/bin/oxDNA input
```

**Nota Bene:** if you copy the files somewhere else you'll also have to update the `plugin_search_path` values specified in the input files.

## Instructions for `FFS`

Read the `FFS/README.md`.