"""EXAMPLE for remote_server.py: serve CL-0 itself from ANOTHER venv (~/venvs/cl0).  Used to validate the REMOTE bridge: results must match in-process CL0.

    env -u PYTHONPATH ~/venvs/cl0/bin/python arena/remote_server.py --factory arena.methods.examples.remote_cl0:make_method --name CL0 --port 6001 \
        --path arena --path cl0
"""
from cl0.config import config_from_dict
from cl0.system import build_stack


def make_method(info):
    cfg = config_from_dict(info["cfg"])
    return build_stack(cfg, info["calib_path"], info["background_path"]).ctrl
