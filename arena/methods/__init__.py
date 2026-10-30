"""Methods of the arena.  Importing this package registers CL0, NOOP and ORACLE; see base.py for the contract and how to plug in your own."""
from .base import REGISTRY, MethodContext, MethodSpec, check_contract, register, resolve  # noqa: F401
from . import cl0, noop, oracle, remote, yawfeasible  # noqa: F401  (registration side effects)
