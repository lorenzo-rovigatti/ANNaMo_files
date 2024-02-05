import numpy as np
import oxpy
import sys, os, time, glob
from multiprocessing import Value, Array, Process, Queue
import ffs_utils as fu

def runner(idx, q, ctrl):
    rng = np.random.default_rng([ctrl.options["initial_seed"], idx])
    while True:
        if q.empty():
            return
    
        idx_sim = q.get()
        simulate(idx_sim, ctrl, rng)

def simulate(idx, ctrl, rng):
    input_filename = ctrl.options["input"]
    initial_seed = ctrl.options["initial_seed"]
    model = ctrl.model
    interface = ctrl.interface
    
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

        # pick a random configuration
        conf_index = rng.integers(0, len(ctrl.starting_confs))
        my_input["conf_file"] = ctrl.starting_confs[conf_index]
        with ctrl.attempt_count.get_lock():
            ctrl.attempt_count.value += 1
            ctrl.attempt_from[conf_index] += 1
            
        manager = oxpy.OxpyManager(my_input)
        config_info = manager.config_info()
        conf_obs = config_info.get_observable_by_id("success_conf")
            
        # list of pairs of pointers to the particles that make up the native contacts
        native_contacts = list(map(lambda pair: [config_info.particles()[pair[0]], config_info.particles()[pair[1]]], model.native_contact_ids))
            
        current_state, current_ops = model.state_ops(config_info, native_contacts)
        done = False

        while not done:
            manager.run(1)

            new_state, new_ops = model.state_ops(config_info, native_contacts)
            new_ops_string = ", ".join([f"{k} == {v}" for k, v in new_ops.items()])
            
            if manager.current_step % 1e6 == 0:
                fu.log(new_ops_string, process=idx, step=manager.current_step)

            if new_state != current_state:
                fu.log(f"crossing {current_state} --> {new_state} ({new_ops_string})", process=idx, step=manager.current_step, if_verbose=True)
                # failure
                if new_state == ctrl.options["state_A"]:
                    fu.log(f"failure (back to Q == Q_A)", process=idx, step=manager.current_step)
                    done = True
                # success
                elif interface.crossed(current_state, new_state):
                    conf = conf_obs.get_output_string(manager.current_step)
                    with ctrl.success_count.get_lock():
                        with open(f"success_{ctrl.success_count.value}.dat", "w") as f:
                            f.write(conf + "\n")
                        ctrl.success_count.value += 1
                        ctrl.success_from[conf_index] += 1
                    fu.log(f"interface crossed ({ctrl.success_count.value} successes)", process=idx, step=manager.current_step)
                    done = True
                
                current_state = new_state
                

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage is {sys.argv[0]} input")
        exit(1)

    ctrl = fu.FFSController(sys.argv[1])
    ctrl.model = fu.nNxB(ctrl.options)

    ctrl.starting_confs = glob.glob(ctrl.options["starting_conf_pattern"])
    fu.log("Main: Found %d configurations with pattern: %s" % (len(ctrl.starting_confs), ctrl.options["starting_conf_pattern"]))
    if len(ctrl.starting_confs) < 1:
        print("0 starting configurations! aborting", file=sys.stderr)
        sys.exit(1)

    ctrl.attempt_count = Value("i", 0)
    ctrl.success_from = Array("i", len(ctrl.starting_confs))
    ctrl.attempt_from = Array("i", len(ctrl.starting_confs))
        
    q = Queue()
    for i in range(ctrl.options["total_simulations"]):
        q.put(i)
  
    processes = []
    for i in range(ctrl.options["ncpus"]):
        p = Process(target=runner, args=(i, q, ctrl))
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

    nsuccesses = ctrl.success_count.value

    fu.log("-------")
    fu.log("SUMMARY")
    fu.log("-------")
    fu.log("nsuccesses: %d nattempts: %d success_prob: %g" % (nsuccesses, ctrl.attempt_count.value, nsuccesses / ctrl.attempt_count.value))

    # print per-configuration statistics
    with open("conf_statistics.log", "w") as out:
        out.write("# log of successes probabilities from each starting conf\n")
        out.write("# idx nsuccesses nattempts prob\n")
        for k, v in enumerate(ctrl.success_from):
            txt = "%3d    %3d    %3d   " % (k, v, ctrl.attempt_from[k])
            if ctrl.attempt_from[k] > 0:
                txt += '%g' % (v / ctrl.attempt_from[k])
            else:
                txt += 'NA'
            out.write(txt + "\n")
