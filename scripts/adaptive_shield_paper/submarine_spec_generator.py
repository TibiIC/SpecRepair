import argparse
import math


def generate_submarine_spec(depth_actual: int, oxygen: int) -> str:
    # Submarine moves 4 depth levels in one step
    depth_symbolic = math.ceil(depth_actual / 4)
    # Oxygen and depth can be represented in binary
    oxygen_bits = math.ceil(math.log2(oxygen+1))
    depth_bits = math.ceil(math.log2(depth_symbolic+1))
    out = "module Submarine\n\n"
    # Define system variables
    sys_vars = []
    out += "sys boolean up;\n"; sys_vars.append("up")
    out += "sys boolean down;\n"; sys_vars.append("down")
    for i in range(depth_symbolic):
        out += f"sys boolean rescues{i+1};\n"
        sys_vars.append(f"rescues{i+1}")
    # Define environment variables
    env_vars = []
    for i in range(depth_symbolic):
        out += f"env boolean diver_at_depth{i+1};\n"
        env_vars.append(f"diver_at_depth{i+1}")
    for i in range(oxygen_bits):
        out += f"env boolean oxygen{i};\n"
        env_vars.append(f"oxygen{i}")
    for i in range(depth_bits):
        out += f"env boolean depth{i};\n"
        env_vars.append(f"depth{i}")
    out += "\n"
    # Define initial environment assumption
    out += "assumption -- surface_start\n"
    out += f"\tini {' & '.join([f'{var}=false' for var in env_vars])};\n"
    # Define oxygen increasing at surface
    sub_at_surface = ' & '.join([f'depth{i}=false' for i in range(depth_bits)])
    for i in range(oxygen):
        oxygen_level_in_bits = ' & '.join([f'oxygen{j}=true' if (i & (1 << j)) else f'oxygen{j}=false' for j in range(oxygen_bits)])
        next_oxygen_level_in_bits = ' & '.join([f'oxygen{j}=true' if ((i+1) & (1 << j)) else f'oxygen{j}=false' for j in range(oxygen_bits)])
        out += f"assumption -- oxygen_increases_at_surface_from_{i}_to_{i+1}\n"
        out += f"\talw({oxygen_level_in_bits} & {sub_at_surface} -> next({next_oxygen_level_in_bits}));\n"
    # Define max oxygen staying same at surface
    out += f"assumption -- max_oxygen_at_surface_stays_max\n"
    max_oxygen_level_in_bits = ' & '.join([f'oxygen{j}=true' if ((oxygen) & (1 << j)) else f'oxygen{j}=false' for j in range(oxygen_bits)])
    out += f"\talw({max_oxygen_level_in_bits} & {sub_at_surface} -> next({max_oxygen_level_in_bits}));\n"
    # Define oxygen decreasing at depths
    sub_at_depth = ' | '.join([f'depth{i}=true' for i in range(depth_bits)])
    # Define oxygen decreasing at depths from max to 1
    for i in range(oxygen, 0, -1):
        oxygen_level_in_bits = ' & '.join([f'oxygen{j}=true' if (i & (1 << j)) else f'oxygen{j}=false' for j in range(oxygen_bits)])
        next_oxygen_level_in_bits = ' & '.join([f'oxygen{j}=true' if ((i - 1) & (1 << j)) else f'oxygen{j}=false' for j in range(oxygen_bits)])
        out += f"assumption -- oxygen_decreases_at_depth_from_{i}_to_{i - 1}\n"
        out += f"\talw({oxygen_level_in_bits} & ({sub_at_depth}) -> next({next_oxygen_level_in_bits}));\n"
    # Define min oxygen staying same at depth
    out += f"assumption -- min_oxygen_at_depth_stays_min\n"
    min_oxygen_level_in_bits = ' & '.join([f'oxygen{j}=false' for j in range(oxygen_bits)])
    out += f"\talw({min_oxygen_level_in_bits} & ({sub_at_depth}) -> next({min_oxygen_level_in_bits}));\n"
    out += "\n"
    # Define system actions and their effect on environment
    # Going down increases depth
    for i in range(depth_symbolic):
        depth_level_in_bits = ' & '.join([f'depth{j}=true' if (i & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        next_depth_level_in_bits = ' & '.join([f'depth{j}=true' if ((i + 1) & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        out += f"assumption -- going_down_increases_depth_from_{i}_to_{i+1}\n"
        out += f"\talw({depth_level_in_bits} & down=true -> next({next_depth_level_in_bits}));\n"
    # Going down at max depth stays at max depth
    max_depth_level_in_bits = ' & '.join([f'depth{j}=true' if ((depth_symbolic) & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
    out += f"assumption -- going_down_at_max_depth_stays_at_max_depth\n"
    out += f"\talw({max_depth_level_in_bits} & down=true -> next({max_depth_level_in_bits}));\n"
    # Going up decreases depth
    for i in range(depth_symbolic, 0, -1):
        depth_level_in_bits = ' & '.join([f'depth{j}=true' if (i & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        next_depth_level_in_bits = ' & '.join([f'depth{j}=true' if ((i - 1) & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        out += f"assumption -- going_up_decreases_depth_from_{i}_to_{i-1}\n"
        out += f"\talw({depth_level_in_bits} & up=true -> next({next_depth_level_in_bits}));\n"
    # Going up at surface stays at surface
    min_depth_level_in_bits = ' & '.join([f'depth{j}=false' for j in range(depth_bits)])
    out += f"assumption -- going_up_at_surface_stays_at_surface\n"
    out += f"\talw({min_depth_level_in_bits} & up=true -> next({min_depth_level_in_bits}));\n"
    # Not moving at each depth keeps depth
    for i in range(depth_symbolic + 1):
        depth_level_in_bits = ' & '.join([f'depth{j}=true' if (i & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        out += f"assumption -- not_moving_keeps_depth_at_{i}\n"
        out += f"\talw({depth_level_in_bits} & up=false & down=false -> next({depth_level_in_bits}));\n"
    out += "\n"
    # JUSTICE environment goal: there's always going to be divers at each high depth
    for i in range(depth_symbolic):
        out += f"assumption -- alwEv_divers_at_depth_{i+1}\n"
        out += f"\talwEv(diver_at_depth{i+1}=true);\n"
    # Success: when submarine reaches depth of divers, they get rescued
    for i in range(depth_symbolic):
        depth_level_in_bits = ' & '.join([f'depth{j}=true' if ((i + 1) & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        out += f"assumption -- diver_gets_rescued_if_submarine_depth_{i + 1}\n"
        out += f"\talw({depth_level_in_bits}->next(diver_at_depth{i+1}=false));\n"
    # Divers are persistent
    for i in range(depth_symbolic):
        depth_level_in_bits = ' & '.join([f'depth{j}=true' if ((i + 1) & (1 << j)) else f'depth{j}=false' for j in range(depth_bits)])
        out += f"assumption -- persistent_diver_at_depth_{i + 1}\n"
        # TODO: convert this to DNF before using in spec repair, for ease
        out += f"\talw(diver_at_depth{i+1}=true & !({depth_level_in_bits})->next(diver_at_depth{i+1}=true));\n"
    out += "\n"
    # System guarantees
    # Submarine not moving in beginning
    out += "guarantee -- submarine_not_moving_in_beginning\n"
    out += f"\tini {' & '.join([f'{var}=false' for var in sys_vars])};\n"
    # If oxygen is false, no action is possible
    min_oxygen_level_in_bits = ' & '.join([f'oxygen{j}=false' for j in range(oxygen_bits)])
    out += "guarantee -- oxygen_false_no_action\n"
    out += f"\talw({min_oxygen_level_in_bits}->up=false & down=false);\n"
    # Cannot go up and down at the same time
    out += "guarantee -- cannot_go_up_and_down_at_same_time\n"
    out += f"\talw(up=false | down=false);\n"
    # Divers gets rescued only if divers at depth become false from true
    for i in range(depth_symbolic):
        out += f"guarantee -- rescue{i+1}_when_diver_at_depth{i+1}_false\n"
        out += f"\talw(PREV(diver_at_depth{i+1}=true) & diver_at_depth{i+1}=false -> rescues{i+1}=true);\n"
        out += f"guarantee -- rescue{i+1}_false_otherwise\n"
        out += f"\talw(PREV(diver_at_depth{i+1}=false) | diver_at_depth{i+1}=true -> rescues{i+1}=false);\n"
    # JUSTICE system goal: always eventually rescue all divers
    for i in range(depth_symbolic):
        out += f"guarantee -- alwEv_rescue_diver_at_depth_{i+1}\n"
        out += f"\talwEv(rescues{i+1}=true);\n"

    return out




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Submarine specification generator')
    parser.add_argument('-d', '--depth', type=int, help='Depth as integer')
    parser.add_argument('-o', '--oxygen', type=int, help='Oxygen as integer')

    args = parser.parse_args()

    if args.depth is not None and args.oxygen is not None:
        depth = args.depth
        oxygen = args.oxygen
    else:
        depth = 96
        oxygen = 64

    spec: str = generate_submarine_spec(depth_actual=depth, oxygen=oxygen)
    print(spec)