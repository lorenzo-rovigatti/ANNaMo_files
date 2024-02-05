import sys
import math
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

with open("ffs.toml", "rb") as f:
    N_CPUs = (tomllib.load(f)["ncpus"])

time_sqr = 0
time_avg = 0
N_successes = 0
current_time = [0, ] * N_CPUs
with open("ffs.log", "r") as f:
    for line in f.readlines():
        if "interface crossed going forwards" in line:
            spl = line.split()
            process = int(spl[1][:-1])
            t = int(spl[3][:-1])
            delta_t = t - current_time[process]
            current_time[process] = t
            time_avg += delta_t
            time_sqr += delta_t**2
            N_successes += 1
        elif "restarting" in line:
            process = int(spl[1][:-1])
            current_time[process] =  0

time_sqr /= N_successes
time_avg /= N_successes
std_dev = math.sqrt(time_sqr - time_avg**2)
error = std_dev / math.sqrt(N_successes)
print(error, std_dev, N_successes, time_avg)
