"""A trivial method for testing the transport: reads the frame, returns the current joints unchanged (no GPU, no model)."""
import numpy as np
from remote_server import Command, TrialEvent


class Dummy:
    phase = "DUMMY"

    def __init__(self):
        self.reset(0.0, None)

    def reset(self, t0, state):
        self.finished, self.outcome, self.events, self.log, self.diag = False, "", [], [], {"n": 0}
        self.n = 0

    def step(self, t, frame, belt, state):
        self.n += 1; self.diag["n"] = self.n
        s = float(np.asarray(frame.img, np.float32).mean()) if frame is not None else -1.0       # touch the pixels like a detector would
        if self.n == 3:
            self.events.append(TrialEvent(t, "dummy", {"mean": s}))
        return Command(np.asarray(state.q_deg, float), 40.0, "DUMMY")


def make_method(info):
    return Dummy()
