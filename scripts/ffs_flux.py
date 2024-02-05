import numpy as np
import oxpy
import sys, os, time
from multiprocessing import Value, Array, Process
import ffs_utils as fu

def simulate(idx, ctrl):
    input_filename = ctrl.options["input"]
    initial_seed = ctrl.options["initial_seed"]
    desired_success_count = ctrl.options["desired_success_count"]
    model = ctrl.model
    interface = ctrl.interface
    
    rng = np.random.default_rng([initial_seed, idx])
    # we may have to run multiple simulations since if a simulation crosses an interface that's beyond the one we are
    # considering we will kill it and start a new one
    while ctrl.success_count.value < desired_success_count:
        with oxpy.Context():
            my_input = oxpy.InputFile()
            my_input.init_from_filename(input_filename)
            my_input["print_conf_interval"] = "1e20" # we don't need to save configurations
            my_input["print_energy_every"] = "1e20" # nor to print the energy

            # remove all observables
            for key in my_input.keys():
                if "data_output" in key:
                    del my_input[key]

            my_input["seed"] = str(rng.integers(0, 2**31))
            fu.log("seed: " + my_input["seed"], process=idx)
            my_input["data_output_1"] = ctrl.options["conf_obs_string"]
            my_input["refresh_vel"] = "true"
            my_input["restart_step_counter"] = "true"
            
            manager = oxpy.OxpyManager(my_input)
            config_info = manager.config_info()
            conf_obs = config_info.get_observable_by_id("success_conf")
            
            # list of pairs of pointers to the particles that make up the native contacts
            native_contacts = list(map(lambda pair: [config_info.particles()[pair[0]], config_info.particles()[pair[1]]], model.native_contact_ids))
            
            current_state, current_ops = model.state_ops(config_info, native_contacts)
            A_recent = True
            done = False
            dt = 0

            while ctrl.success_count.value < desired_success_count and not done:
                manager.run(1)
                dt += 1

                new_state, new_ops = model.state_ops(config_info, native_contacts)
                new_ops_string = ", ".join([f"{k} == {v}" for k, v in new_ops.items()])

                if manager.current_step % 1e6 == 0:
                    fu.log(new_ops_string, process=idx, step=manager.current_step)
                
                if new_state != current_state:
                    fu.log(f"crossing {current_state} --> {new_state} ({new_ops_string})", process=idx, step=manager.current_step, if_verbose=True)
                    if new_state == ctrl.options["state_A"]:
                        A_recent = True
                    elif interface.crossed(current_state, new_state):
                        # if we visited A more recently than we crossed the interface then this is a proper forward crossing
                        if A_recent:
                            conf = conf_obs.get_output_string(dt) # we use the time elapsed since the last success as the timestep
                            with ctrl.success_count.get_lock(), ctrl.success_times.get_lock(), ctrl.success_times_sqr.get_lock():
                                with open(f"success_{ctrl.success_count.value}.dat", "w") as f:
                                    f.write(conf + "\n")
                                ctrl.success_count.value += 1
                                ctrl.success_times[idx] += dt
                                ctrl.success_times_sqr[idx] += dt**2
                                
                                fu.log(f"interface crossed going forwards ({ctrl.success_count.value} successes)", process=idx, step=manager.current_step)
                            dt = 0
                            A_recent = False
                        else:
                            fu.log(f"interface crossed without having gone back to A", process=idx, step=manager.current_step)
                    elif new_state > interface.Q_right:
                        fu.log(f"crossed to the next state (Q == {new_state}), stopping and restarting", process=idx, step=manager.current_step)
                        done = True
                        del manager
                        del my_input
                
                    current_state = new_state

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage is {sys.argv[0]} input")
        exit(1)

    ctrl = fu.FFSController(sys.argv[1])
    ctrl.model = fu.nNxB(ctrl.options)
    ctrl.success_times = Array("i", ctrl.options["ncpus"])
    ctrl.success_times_sqr = Array("q", ctrl.options["ncpus"])
  
    processes = []
    for i in range(ctrl.options["ncpus"]):
        p = Process(target=simulate, args=(i, ctrl))
        processes.append(p)
	
    tp = Process(target=fu.timer, args=(ctrl.success_count, ))
    tp.start()
    fu.log(f"Main: Starting {ctrl.options['ncpus']} processes...")
    for p in processes:
        p.start()
	
    fu.log("Main: waiting for processes to finish")
    for p in processes:
        p.join()
	
    fu.log("Main: Terminating timer")
    tp.kill()

    avg_timesteps = np.sum(ctrl.success_times) / ctrl.success_count.value
    avg_timesteps_sqr = np.sum(ctrl.success_times_sqr) / ctrl.success_count.value
    std_dev = np.sqrt(avg_timesteps_sqr - avg_timesteps**2)

    fu.log("-------")
    fu.log("SUMMARY")
    fu.log("-------")
    fu.log(f"Average number of timesteps taken to reach a success (aka 1 / flux): {avg_timesteps}")
    fu.log(f"Average number of timesteps standard deviation: {std_dev}")
    fu.log(f"Initial flux: {1 / avg_timesteps}")
