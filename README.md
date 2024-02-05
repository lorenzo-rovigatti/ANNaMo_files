# ANNaMo_files

Code and examples for the ANNaMo model.

## The simulation code

ANNaMo simulations are run with [oxDNA](https://github.com/lorenzo-rovigatti/oxDNA). The repository contains a snapshot dated 05/02/2024, which can be compiled with the following commands:

```
cd oxDNA
mkdir build
cd build
cmake ..
make -j6
make rovigatti tostiguerra -j6
```

At the end of the compilation stage, the `oxDNA` executable will be placed in the `build/bin` folder. Check the [oxDNA docs](https://lorenzo-rovigatti.github.io/oxDNA/) for additional information.

Note that `ANNaMo` is implemented as an [oxDNA plugin](https://lorenzo-rovigatti.github.io/oxDNA/input.html#plugins-options), which means that input files should contain the correct `plugin_search_path`s (see below for more information).
