#!/bin/bash

cd FLUX
python3 ../../../FFS/ffs_flux.py ffs.toml

cd ../SHOOT_1
python3 ../../../FFS/ffs_shoot.py ffs.toml

cd ../SHOOT_2
python3 ../../../FFS/ffs_shoot.py ffs.toml

cd ../SHOOT_3
python3 ../../../FFS/ffs_shoot.py ffs.toml

cd ../SHOOT_4
python3 ../../../FFS/ffs_shoot.py ffs.toml
