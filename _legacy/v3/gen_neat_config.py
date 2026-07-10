"""Generate a valid neat-python 1.1.0 config by trial and error"""
import neat
import tempfile, os

base = """[NEAT]
fitness_criterion        = max
fitness_threshold        = 0.95
pop_size                 = 30
reset_on_extinction      = False
no_fitness_termination   = True

[DefaultGenome]
activation_default      = sigmoid
activation_mutate_rate  = 0.05
activation_options      = sigmoid tanh relu
aggregation_default     = sum
aggregation_mutate_rate = 0.05
aggregation_options     = sum
bias_init_mean          = 0.0
bias_init_stdev         = 1.0
bias_init_type          = gaussian
bias_max_value          = 3.0
bias_min_value          = -3.0
bias_mutate_power       = 0.5
bias_mutate_rate        = 0.7
bias_replace_rate       = 0.1
compatibility_disjoint_coefficient = 1.0
compatibility_weight_coefficient   = 0.5
conn_add_prob           = 0.3
conn_delete_prob        = 0.2
enabled_default         = True
enabled_mutate_rate     = 0.01
feed_forward            = True
initial_connection      = full_direct
single_structural_mutation = false
structural_mutation_surer  = default
node_add_prob           = 0.15
node_delete_prob        = 0.1
num_hidden              = 0
num_inputs              = 5
num_outputs             = 3
response_init_mean      = 1.0
response_init_stdev     = 0.0
response_init_type      = gaussian
response_max_value      = 3.0
response_min_value      = -3.0
response_mutate_power   = 0.0
response_mutate_rate    = 0.0
response_replace_rate   = 0.0
weight_init_mean        = 0.0
weight_init_stdev       = 1.0
weight_init_type        = gaussian
weight_max_value        = 3.0
weight_min_value        = -3.0
weight_mutate_power     = 0.5
weight_mutate_rate      = 0.8
weight_replace_rate     = 0.1

[DefaultSpeciesSet]
compatibility_threshold = 3.0

[DefaultStagnation]
species_fitness_func = max
max_stagnation       = 15
species_elitism      = 2

[DefaultReproduction]
elitism            = 2
survival_threshold = 0.2
min_species_size   = 2
"""

for _ in range(20):
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    tmp.write(base)
    tmp.close()
    try:
        cfg = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                          neat.DefaultSpeciesSet, neat.DefaultStagnation, tmp.name)
        print("SUCCESS! Config is valid.")
        print("--- FINAL CONFIG ---")
        print(base)
        break
    except Exception as e:
        msg = str(e)
        print(f"Missing: {msg}")
        # Extract param name and suggested value
        if "Suggested value:" in msg:
            suggestion = msg.split("Suggested value:")[1].strip()
            param = suggestion.split("=")[0].strip()
            # Add to DefaultGenome section
            section = "[DefaultGenome]"
            if "DefaultReproduction" in msg:
                section = "[DefaultReproduction]"
            elif "DefaultStagnation" in msg:
                section = "[DefaultStagnation]"
            elif "DefaultSpeciesSet" in msg:
                section = "[DefaultSpeciesSet]"
            elif "NEAT" in msg and "DefaultGenome" not in msg:
                section = "[NEAT]"
            
            # Insert after section header
            base = base.replace(section, f"{section}\n{suggestion}")
            print(f"  -> Added: {suggestion}")
    finally:
        os.unlink(tmp.name)
