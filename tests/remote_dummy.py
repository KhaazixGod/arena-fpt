"""A tiny method for the remote-bridge test: closes the gripper on the 3rd step, finishes on the 5th, reports what it saw."""
from cl0.types import Command, TrialEvent


class Dummy:
    def __init__(self, info):
        self.info = info

    def reset(self, t0, state):
        self.n, self.finished, self.outcome = 0, False, ""
        self.events, self.log, self.diag = [TrialEvent(t0, "phase:DUMMY", {"w": self.info["image_size"][0]})], [], {"frames": 0}
        self.phase = "DUMMY"

    def step(self, t, frame, belt, state):
        self.n += 1
        if frame is not None:
            self.diag["frames"] += 1
            self.diag["px"] = int(frame.img[0, 0, 0])
            self.diag["s_img"] = belt.s_at(frame.t_capture)
        self.diag["s_now"] = belt.s_at(t)
        if self.n == 5:
            self.finished, self.outcome = True, "dummy_done"
            self.events.append(TrialEvent(t, "phase:DONE", {}))
        return Command(state.q_deg + 1.0, 0.0 if self.n >= 3 else None, "DUMMY")


def make_method(info):
    return Dummy(info)
