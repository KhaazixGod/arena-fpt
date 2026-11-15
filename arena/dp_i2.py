"""Interface I2 for Diffusion Policy (paper-dev; KE_HOACH_PAPER.md P4): relative belt-frame actions exactly like ACT_I2 (train_act_i2.py), for a policy
that looks at n_obs_steps > 1 observations.

LeRobot 0.6.1's RelativeActionsProcessorStep subtracts observation.state from the action chunk.  In Diffusion Policy's training batches the state is
(B, n_obs_steps, D) while the chunk is (B, horizon, D): the in-place subtraction does not broadcast.  RelativeActionsLastObsStep uses the LAST observation
step as the reference (the step the predicted chunk starts from; LeRobot's DP predicts actions from index n_obs_steps - 1 on) and gives the model the full
observation history.  At inference the policy receives one observation per call, so the step is RelativeActionsProcessorStep unchanged, and its cached
state (the newest one) turns the chunk back into absolute targets.  The step is registered, so a saved checkpoint loads with LeRobot's stock
make_pre_post_processors once this module is imported (arena/methods/diffusion_i2.py does).
"""
from __future__ import annotations

from dataclasses import dataclass

from lerobot.lerobot_types import TransitionKey
from lerobot.processor.factory import make_default_policy_processor_steps, make_policy_processor_pipelines
from lerobot.processor.pipeline import ProcessorStepRegistry
from lerobot.processor.relative_action_processor import AbsoluteActionsProcessorStep, RelativeActionsProcessorStep
from lerobot.utils.constants import OBS_STATE

from arena.i2 import NAMES, RELATIVE_EXCLUDE


@ProcessorStepRegistry.register("relative_actions_last_obs")
@dataclass
class RelativeActionsLastObsStep(RelativeActionsProcessorStep):
    def __call__(self, transition):
        obs = transition.get(TransitionKey.OBSERVATION) or {}
        state = obs.get(OBS_STATE)
        action = transition.get(TransitionKey.ACTION)
        if state is not None and action is not None and state.ndim == 3 and action.ndim == 3:     # training batch (B, n_obs, D) vs (B, horizon, D)
            t2 = transition.copy()
            t2[TransitionKey.OBSERVATION] = {**obs, OBS_STATE: state[:, -1]}
            out = super().__call__(t2)
            out[TransitionKey.OBSERVATION] = obs
            return out
        return super().__call__(transition)


def make_dp_i2_pre_post_processors(config, dataset_stats=None):
    """The pi0-style order of train_act_i2.py: raw -> relative -> normalise -> model -> unnormalise -> absolute."""
    rel = RelativeActionsLastObsStep(enabled=True, exclude_joints=list(RELATIVE_EXCLUDE), action_names=list(NAMES))
    s = make_default_policy_processor_steps(config, dataset_stats, normalizer_device=config.device)
    return make_policy_processor_pipelines(
        input_steps=[s.rename_observations, s.add_batch_dim, s.to_device, rel, s.normalize],
        output_steps=[s.unnormalize, AbsoluteActionsProcessorStep(enabled=True, relative_step=rel), s.to_cpu],
    )
