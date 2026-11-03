"""IsaacPlatform timing on a fake world: ticks are whole physics steps, frames arrive latency_true_s after capture and carry
t_capture = delivery - camera.latency_s, the belt readout follows the true profile within pulse quantisation + serial delay."""
import math

import numpy as np


def test_tick_is_whole_steps(fake_platform):
    plat, w = fake_platform
    plat.reset_trial([])
    k0 = plat.k0
    for i in range(1, 21):
        t = plat.wait_tick()
        assert w.k - k0 == 6 * i
        assert math.isclose(t, 6 * i / 300.0, abs_tol=1e-12)


def test_frame_latency_and_timestamp(fake_platform, arena_cfg, scene_cfg):
    plat, w = fake_platform
    plat.reset_trial([])
    k0 = plat.k0
    lat_true, lat_est = scene_cfg["camera"]["latency_true_s"], arena_cfg.camera.latency_s
    got = []
    for _ in range(60):
        plat.wait_tick()
        fr = plat.poll_frame()
        if fr is not None:
            k_cap = int(fr.img[0, 0])
            t_cap_true = (k_cap - k0) / 300.0
            assert (k_cap - k0) % 10 == 0                                       # 30 fps = every 10 steps
            assert w.k - k_cap >= 30                                            # not before it was delivered
            assert math.isclose(fr.t_capture - t_cap_true, lat_true - lat_est, abs_tol=1e-9)
            got.append(k_cap)
    assert len(got) >= 20 and got == sorted(got)
    assert got[0] == k0                                                         # the frame of t = 0 arrives first


def test_poll_returns_only_newest(fake_platform):
    plat, w = fake_platform
    plat.reset_trial([])
    for _ in range(30):
        plat.wait_tick()                                                         # 180 steps: several frames delivered, none polled
    fr = plat.poll_frame()
    assert fr is not None and w.k - int(fr.img[0, 0]) < 40                       # the newest, not the oldest
    assert plat.poll_frame() is None


def test_belt_counter_follows_true_profile(fake_platform, arena_cfg):
    plat, w = fake_platform
    plat.reset_trial([])
    plat.start_belt(60.0)
    for _ in range(150):                                                         # 3 s
        plat.wait_tick()
    t = plat.now()
    s_true, s_read = plat.belt_s_true(t), plat.belt.s_at(t)
    assert abs(s_read - s_true) <= 0.05 + 60.0 * (0.003 + 0.01) + 1e-6
    assert abs(plat.belt.speed_at(t) - 60.0) < 1.0
    assert abs(w.belt_v - 60.0) < 1e-6                                           # PhysX surface speed reached the command
    first_moving = next(i for i, v in enumerate(w.belt_v_log[-150 * 6:]) if v > 0)
    assert first_moving >= int(arena_cfg.belt.cmd_delay_s * 300) - 1             # the belt does not move before the command delay


def test_reset_rejects_flung_object(fake_platform):
    from arena.world import SimFault
    plat, w = fake_platform
    orig = w.gt_objects
    w.gt_objects = lambda: {n: {**o, "a_mm": o["a_mm"] + 10.0} for n, o in orig().items()}
    try:
        plat.reset_trial([{"name": "cube35", "a_mm": 0.0, "b_mm": -180.0, "yaw_deg": 0.0}])
        raised = False
    except SimFault:
        raised = True
    assert raised


def test_depth_reaches_frame_and_image(fake_platform):
    """pixel_grasp gets only frame.img from cl0's controller, so the depth must travel on the image too."""
    plat, w = fake_platform
    w.depth_enabled, plat.depth = True, True
    w.last_depth_mm = lambda: np.full((1, 1), 500.0)
    plat.reset_trial([])
    fr = None
    for _ in range(10):
        plat.wait_tick()
        fr = plat.poll_frame() or fr
    assert fr.depth_mm[0, 0] == 500.0 and fr.img.depth_mm[0, 0] == 500.0
