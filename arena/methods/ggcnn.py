"""GGCNN (candidate for baseline CL-2, KE_HOACH_HUONG_1 §3.4): Morrison et al., "Closing the Loop for Robotic Grasping" (RSS 2018), pretrained on the Cornell
depth images, NO training and NO data collection here.  Weights: github.com/dougsm/ggcnn release v0.1 (BSD-3), state dict only, sha256 of the zip 465ef506...  No code of that
repo is executed: the network is re-declared below from its published architecture, and the weights load with weights_only=True.

Depth image -> crop to the belt window -> rescale so one input pixel covers ``mm_per_input_px`` -> subtract the mean, clip to +-1 m (as the repo's normalise(), metres)
-> q, cos2t, sin2t, width -> Gaussian smoothing as the repo's post_process_output -> local maxima of q on points standing above the belt
-> PixelGrasp, then CL-0's tracker, selection and BeltExecutor through arena.methods.pixel_grasp, with yaw-aware feasibility.  Needs run_arena --depth (ideal depth).

Input scale [unverified assumption]: the network has no notion of metric scale; 1.2 mm per input pixel is an estimate for Cornell (Kinect-like camera, about 0.65 m).
Choices made here, not in the paper: the belt window crop, the height gate, the peak search, the capped width.  Parameters: --method-arg ggcnn_mm_per_px=.. ggcnn_min_q=..
"""
from __future__ import annotations

import os

import cv2
import numpy as np

from .base import MethodContext, register
from .pixel_grasp import PixelGrasp, pixel_grasp_method

HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
WEIGHTS = os.path.join(HERE, "third_party", "ggcnn_weights", "ggcnn_weights_cornell", "ggcnn_epoch_23_cornell_statedict.pt")


def load_net():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class GGCNN(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 32, 9, stride=3, padding=3)
            self.conv2 = nn.Conv2d(32, 16, 5, stride=2, padding=2)
            self.conv3 = nn.Conv2d(16, 8, 3, stride=2, padding=1)
            self.convt1 = nn.ConvTranspose2d(8, 8, 3, stride=2, padding=1, output_padding=1)
            self.convt2 = nn.ConvTranspose2d(8, 16, 5, stride=2, padding=2, output_padding=1)
            self.convt3 = nn.ConvTranspose2d(16, 32, 9, stride=3, padding=3, output_padding=1)
            self.pos_output = nn.Conv2d(32, 1, 2)
            self.cos_output = nn.Conv2d(32, 1, 2)
            self.sin_output = nn.Conv2d(32, 1, 2)
            self.width_output = nn.Conv2d(32, 1, 2)

        def forward(self, x):
            for layer in (self.conv1, self.conv2, self.conv3, self.convt1, self.convt2, self.convt3):
                x = F.relu(layer(x))
            return self.pos_output(x), self.cos_output(x), self.sin_output(x), self.width_output(x)

    net = GGCNN()
    net.load_state_dict(torch.load(WEIGHTS, map_location="cpu", weights_only=True))
    return net.eval()


class GGCNNDetector:
    def __init__(self, calib, window_px, mm_per_input_px: float = 1.2, min_q: float = 0.3, min_height_mm: float = 3.0, max_peaks: int = 8, net=None, max_width_mm: float = 56.0):
        self.calib, self.win = calib, window_px                 # (u0, v0, u1, v1) of the belt window in the camera image
        self.mm_px, self.min_q, self.min_h, self.max_peaks = mm_per_input_px, min_q, min_height_mm, max_peaks
        self.net = net or load_net()
        self.max_width_mm, self.last_widths_mm = max_width_mm, []
        u0, v0, u1, v1 = window_px
        self.scale = calib.mm_per_pixel_at((0.5 * (u0 + u1), 0.5 * (v0 + v1))) / mm_per_input_px      # input pixels per camera pixel

    def infer(self, depth_mm: np.ndarray):
        """q, angle (rad, image frame), width (input px) and the rescaled depth (mm), all the same size."""
        import torch
        u0, v0, u1, v1 = self.win
        d = cv2.resize(depth_mm[v0:v1, u0:u1].astype(np.float32), None, fx=self.scale, fy=self.scale, interpolation=cv2.INTER_AREA)
        h, w = d.shape
        d = d[: h - h % 12, : w - w % 12]                        # the stride product is 12
        fin = np.isfinite(d)
        if not fin.all():
            d = np.where(fin, d, np.median(d[fin]))
        m = d * 1e-3
        x = torch.from_numpy(np.clip(m - m.mean(), -1.0, 1.0)[None, None].astype(np.float32))
        with torch.no_grad():
            q, c, s, wd = self.net(x)
        ang = (torch.atan2(s, c) / 2.0).numpy().squeeze()
        blur = lambda a, sig: cv2.GaussianBlur(a.astype(np.float32), (0, 0), sig, borderType=cv2.BORDER_REPLICATE)
        q = blur(q.numpy().squeeze(), 2.0)
        ang = blur(ang, 2.0)
        wd = blur(wd.numpy().squeeze() * 150.0, 1.0)
        if q.shape != d.shape:
            raise RuntimeError(f"GG-CNN output {q.shape} != input {d.shape}")
        return q, ang, wd, d

    def __call__(self, img_bgr, depth_mm):
        if depth_mm is None:
            raise RuntimeError("GGCNN needs depth: run_arena --depth")
        q, ang, wd, d = self.infer(depth_mm)
        belt = float(np.median(d))
        peak = (q == cv2.dilate(q, np.ones((15, 15), np.uint8))) & (q >= self.min_q) & (d < belt - self.min_h)      # local maxima standing above the belt
        vs, us = np.nonzero(peak)
        order = np.argsort(-q[vs, us])[: self.max_peaks]
        out = []
        for i in order:
            v, u = int(vs[i]), int(us[i])
            # the predicted width follows the Cornell annotators' gripper, not the SO-101 jaws (E7: every detection exceeded 56 mm and was rejected). The jaws open by a fixed
            # amount anyway, so the width is capped instead of used as a reject; the raw values are kept in last_widths_mm.
            self.last_widths_mm.append(float(wd[v, u]) * self.mm_px)
            out.append(PixelGrasp(self.win[0] + u / self.scale, self.win[1] + v / self.scale, float(np.degrees(ang[v, u])) % 180.0, min(float(wd[v, u]) * self.mm_px, self.max_width_mm), float(q[v, u])))
        return out


def belt_window_px(ctx: MethodContext):
    """Camera-image rectangle of CL-0's top-down window, limited to the belt (the window extends 15 mm beyond it on each side; floor depth is far away)."""
    from cl0.perception import BackgroundModel, window_of
    win = window_of(BackgroundModel.load(ctx.background_path))
    phi = np.radians(ctx.calib.belt_dir_deg)
    u_hat, v_hat = np.array([np.cos(phi), np.sin(phi)]), np.array([-np.sin(phi), np.cos(phi)])
    pts = [a * u_hat + b * v_hat for a in (win.a_min, win.a_max) for b in (win.b_min + 15.0, win.b_max - 15.0)]
    px = ctx.calib.world_to_pix(np.array(pts))
    u0, v0 = np.floor(px.min(axis=0)).astype(int) + 2
    u1, v1 = np.ceil(px.max(axis=0)).astype(int) - 2
    return int(u0), int(v0), int(u1), int(v1)


@register("GGCNN", doc="GG-CNN pretrained on Cornell (depth) + CL-0 tracker/executor; no training, no data collection")
def make_ggcnn(ctx: MethodContext):
    e = ctx.extra
    det = GGCNNDetector(ctx.calib, belt_window_px(ctx), float(e.get("ggcnn_mm_per_px", 1.2)), float(e.get("ggcnn_min_q", 0.3)),
                        max_width_mm=ctx.cfg.perception.grasp.gripper_w_mm - ctx.cfg.perception.grasp.width_margin_mm)
    return pixel_grasp_method(ctx, det)
