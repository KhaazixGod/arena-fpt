"""Why CL0 rejects static dev_C3: render each arrangement at home, run the real detector, print reject reasons and component sizes.  Simulation only, no method run."""
import csv,json,os,sys,collections
import numpy as np
HERE="/home/pread/Projects/dir1_tools/arena"
sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(os.path.dirname(HERE),"cl0"))
from isaacsim import SimulationApp
app=SimulationApp({"headless":True,"width":1280,"height":720})
import cv2
from arena import scene as S
from arena.world import IsaacWorld
from arena.platform import IsaacPlatform
from arena.objects_gen import load_catalog as load_specs_sim
from arena.arrangements import to_placements
from cl0.arrangements import read_arrangements
from cl0.config import load_config
from cl0.system import build_stack
OUT=sys.argv[1]; os.makedirs(OUT,exist_ok=True)
sc=S.load_scene_cfg(); cfg=load_config(os.environ.get("PROBE_CONFIG",os.path.join(HERE,"configs","arena.toml")))
specs=load_specs_sim()
w=IsaacWorld(app,specs,sc); plat=IsaacPlatform(w,cfg)
st=build_stack(cfg,os.path.join(HERE,"runs/calib/calib.json"),os.path.join(HERE,"runs/calib/background.npz"),cache_dir=os.path.join(HERE,"runs/calib"))
det=st.ctrl.det
sheet=read_arrangements(os.path.join(HERE,"arrangements/sim/dev_C3.csv"))
sd={s.name:s for s in specs}
for aid in list(sheet)[:20]:
    pl=to_placements(sheet[aid],0.0,sc,w.spec_by_name)
    plat.reset_trial(pl,hard=True)
    img=w.render_bgr()
    r=det.detect(img,0.0)
    rows=[(d.reject or "ok",round(d.area_mm2),round(d.a_mm),round(d.b_mm)) for d in r.dets]
    print(aid,rows,r.info if hasattr(r,'info') else '',flush=True)
    if aid.endswith(('001','002')): cv2.imwrite(f"{OUT}/{aid}.png",img); cv2.imwrite(f"{OUT}/{aid}_mask.png",r.mask if hasattr(r,'mask') else r[1])
app.close()
