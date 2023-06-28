from ableton.v2.control_surface import control_surface as cs
print(cs)

mg = cs.get_control_surfaces()[1]

def print_reg():
    print(mg._forwarding_registry)

