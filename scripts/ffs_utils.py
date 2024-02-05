from multiprocessing import Lock, Value
import math, sys, time
import oxpy
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

    
class Logger:
    def __init__(self):
        self.log_lock = Lock()
        self.verbose = False
        self.also_stderr = False
        self.initialised = False

    def init(self, options):
        # we treat this option in a special way since the dict that takes care of the options uses this class to log errors
        if "log" not in options or "filename" not in options["log"]:
            print("Required key 'log.filename' not found, exiting")
            exit(1)
        
        self.log_file = open(options["log"]["filename"], 'w', 1)

        if "verbose" in options["log"]:
            self.verbose = options["log"]["verbose"]

        if "also_stderr" in options["log"]:
            self.also_stderr = options["log"]["also_stderr"]
            
        self.initialised = True

    def __call__(self, text, process=None, step=None, if_verbose=False):
        if if_verbose and not self.verbose:
            return
        
        if not self.initialised:
            print("Logger unitiliased, exiting", file=sys.stderr)
            exit(1)
        
        if step is not None:
            text = f"step {step}, {text}"
        if process is not None:
            text = f"Process {process}, {text}"
    
        with self.log_lock:
            self.log_file.write(text + '\n')
            if self.also_stderr:
                print(text, file=sys.stderr)

log = Logger()

    
class Interface():
    def __init__(self, Q_left, Q_right):
        if Q_right - Q_left != 1:
            log(f"Interfaces separating states further away than 1 are not supported (Q_left == {Q_left}, Q_right == {Q_right})")
            exit(1)
        
        self.Q_left = Q_left
        self.Q_right = Q_right
    
    def crossed(self, Q1, Q2):
        return Q1 == self.Q_left and Q2 == self.Q_right


class Options(dict):
    default_options = {
        'state_A' : -2,
        'bond_threshold' : -4.0,
        'conf_obs_string' : """{
  name = success.dat
  print_every = 1e20
  only_last = true
  col_1 = {
    type = Configuration
    id = success_conf
  }
}"""
    }
    
    def __init__(self, input_file):
        super().__init__(Options.default_options)

        try:
            with open(input_file, "rb") as f:
                self.update(tomllib.load(f))
        except FileNotFoundError:
            print("Input file not found or not accessible, exiting", file=sys.stderr)
            exit(1)
        except tomllib.TOMLDecodeError:
            print("Input file contains non-valid TOML, exiting", file=sys.stderr)
            exit(1)

    def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            log(f"Option '{key}' not found, exiting")
            exit(1)
            

class FFSController:
    def __init__(self, input_file):
        self.options = Options(input_file)
        log.init(self.options)
        self.interface = Interface(self.options["interface"][0], self.options["interface"][1])

        self.success_count = Value("i", 0)


def timer(success_count):
    timestep = time.asctime(time.localtime())
    log("Timer started at %s" % (timestep))
    itime = time.time()
    while True:
        time.sleep(10)
        now = time.time()
        with success_count.get_lock():
            ns = success_count.value
            if ns > 0:
                log("Timer: at %s: successes: %d, time per success: %g (%g sec elapsed)" % (timestep, ns, (now - itime) / ns, now - itime))
            else:
                log("Timer: at %s: no successes yet" % (timestep))

class nNxB:
    def __init__(self, options):
        self.bond_threshold = options["bond_threshold"]
        self._set_native_contact_ids(options["input"])
        self.state_A = options["state_A"]
    
    def state_ops(self, config_info, pairs):
        box = config_info.box
        dists_sqr = list(map(lambda pair: box.sqr_min_image_distance(pair[0], pair[1]), pairs))
        op_dist = math.sqrt(min(dists_sqr))
        
        interaction = config_info.interaction
        interaction.begin_energy_computation()
        energies = list(map(lambda pair: interaction.pair_interaction_term(2, pair[0], pair[1]), pairs))
        op_bonds = len(list(filter(lambda E: E < self.bond_threshold, energies)))

        if op_dist > 4:
            state = self.state_A
        elif op_dist < 4 and op_dist > 1.6:
            if op_bonds > 0:
                log(f"Disaster! bonds observed in state -1: op_dist == {op_dist}, op_bonds == {op_bonds}")
                exit(1)
            state = -1
        elif op_dist < 1.6 and op_bonds == 0:
            state = 0
        elif op_bonds > 0:
            state = op_bonds
        else: # I don't think this can ever be reached
            log(f"Disaster! Undetermined state op_dist == {op_dist}, op_bonds == {op_bonds}")
            exit(1)

        return state, {"op_dist" : op_dist, "op_bonds" : op_bonds}

    def _set_native_contact_ids(self, input_filename):
        with oxpy.Context():
            my_input = oxpy.InputFile()
            my_input.init_from_filename(input_filename)
            my_input['log_file'] = "/dev/null"
            manager = oxpy.OxpyManager(my_input)
            config_info = manager.config_info()
            N = config_info.N()
            N_strands = len(config_info.molecules())

            if N_strands != 3:
                print(f"Can't work with {N_strands} strands (should be 3)")
                exit(1)

            substrate = config_info.molecules()[0].particles
            protector = config_info.molecules()[1].particles
            invader = config_info.molecules()[2].particles
        
            substrate_ids = list(map(lambda p: p.index, substrate))
            protector_ids = list(map(lambda p: p.index, protector))
            invader_ids = list(map(lambda p: p.index, invader))
        
        # create a list of native contacts
        self.native_contact_ids = list(zip(substrate_ids, reversed(invader_ids)))
