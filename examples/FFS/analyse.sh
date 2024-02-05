#!/bin/bash
		
if [ -s FLUX/ffs.log ]
then
	cd FLUX
	tail -n1 ffs.log | awk '{print $3}' > flux.dat
	python3 ../flux_std_dev.py > error.dat
	awk '{print $1 / $4}' error.dat > relative_error.dat
	cd ..
fi

for sd in $(ls -1d SHOOT_*)
do
	if [ -s $sd/ffs.log ] && grep nsuccesses $sd/ffs.log > /dev/null
	then
		p=$(tail -n1 $sd/ffs.log | awk '{print $6}')
		N=$(grep total_simulations $sd/ffs.toml | awk '{print $3}')
		echo $p  > $sd/prob.dat
		awk -v N=$N '{print sqrt($1*(1-$1) / N) / $1}' $sd/prob.dat > $sd/relative_error.dat
	fi
done

if [ -s SHOOT_1/prob.dat ]
then
	error=$(awk '{a += $1*$1;} END {print sqrt(a);}' */relative_error.dat)
	awk -v error=$error 'BEGIN {a = 1} {a *=$1} END {print a, error * a}' */flux.dat */prob.dat > rate.dat
	awk -v error=$error 'BEGIN {a = 1} {a *=$1} END {print 1 / a, error / a}' */flux.dat */prob.dat > steps.dat
fi

rate=$(awk '{print $1}' rate.dat)
steps=$(awk '{print $1}' steps.dat)
echo "Final rate: $rate (corresponding to $steps steps)"
