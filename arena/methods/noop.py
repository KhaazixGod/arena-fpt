"""NOOP: never moves (lower bound M9).  Any 'success' it gets is an environment artefact (an object launched or carried up by something)."""
from __future__ import annotations

from typing import List

from cl0.types import Command, TrialEvent

from .base import MethodContext, register


class NoopMethod:
    phase = "NOOP"

    def __init__(self, duration_s: float):
        self.duration_s = duration_s
        self.reset(0.0, None)

    def reset(self, t0, state) -> None:
        self.t0, self.finished, self.outcome = t0, False, ""
        self.events: List[TrialEvent] = [TrialEvent(t0, "phase:NOOP", {})]
        self.log: list = []
        self.diag: dict = {}

    def step(self, t, frame, belt, state) -> Command:
        if t - self.t0 >= self.duration_s:
            self.finished, self.outcome = True, "noop"
            self.events.append(TrialEvent(t, "phase:DONE", {}))
        return Command(None, None, "NOOP")

    def close(self) -> None:
        pass


@register("NOOP", doc="does nothing for executor.trial_timeout_s (lower bound)", uses_pixels=False)
def make_noop(ctx: MethodContext):
    return NoopMethod(ctx.cfg.executor.trial_timeout_s)
