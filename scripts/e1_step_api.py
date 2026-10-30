import sys
from isaacsim import SimulationApp
app = SimulationApp({"headless": True, "width": 320, "height": 240})
import omni.physx as ox
pi = ox.get_physx_interface()
for n in ("update_simulation", "update_transformations", "start_simulation", "force_load_physics_from_usd", "is_running", "get_full_contact_report"):
    f = getattr(pi, n, None); print(n, "->", (f.__doc__ or "").strip().splitlines()[:3] if f else None)
si = ox.get_physx_simulation_interface()
print("sim_interface:", [m for m in dir(si) if not m.startswith("_")][:60])
print("stage_update:", [m for m in dir(ox.get_physx_stage_update_interface()) if not m.startswith("_")][:40])
app.close()
