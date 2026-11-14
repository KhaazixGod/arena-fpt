"""Interface I2: `lerobot-train` for ACT with RELATIVE actions on x_b, y_b, z (KE_HOACH_HUONG_1.md §3.2).  Same arguments as lerobot-train.

    env -u PYTHONPATH ~/venvs/lerobot_data/bin/python train_act_i2.py --policy.type=act --dataset.repo_id=local/arena_so101_oracle_i2 \
        --dataset.root=runs/e6_demos_real/lerobot_i2 --output_dir=runs/act_i2_s1000 --seed=1000 --policy.push_to_hub=false ...
LeRobot 0.6.1 wires RelativeActionsProcessorStep only for pi0/pi05/groot; ACT gets the default pipeline.  This swaps ACT's processor factory for the
pi0 order (raw -> relative -> normalise -> model -> unnormalise -> absolute); both steps are in LeRobot's registry, so the saved checkpoint loads with the
stock make_pre_post_processors.  The dataset's action stats must already be relative (to_lerobot_i2.py does it).  The ACT model itself is unchanged.
At inference, convert a whole chunk right after preprocessing ITS observation (methods/act_i2.py): select_action's queue would add a later state.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE]

import lerobot.policies.act.processor_act as processor_act
from lerobot.processor.factory import make_default_policy_processor_steps, make_policy_processor_pipelines
from lerobot.processor.relative_action_processor import AbsoluteActionsProcessorStep, RelativeActionsProcessorStep

from arena.i2 import NAMES, RELATIVE_EXCLUDE


def make_act_i2_pre_post_processors(config, dataset_stats=None):
    rel = RelativeActionsProcessorStep(enabled=True, exclude_joints=list(RELATIVE_EXCLUDE), action_names=list(NAMES))
    s = make_default_policy_processor_steps(config, dataset_stats, normalizer_device=config.device)
    return make_policy_processor_pipelines(
        input_steps=[s.rename_observations, s.add_batch_dim, s.to_device, rel, s.normalize],
        output_steps=[s.unnormalize, AbsoluteActionsProcessorStep(enabled=True, relative_step=rel), s.to_cpu],
    )


processor_act.make_act_pre_post_processors = make_act_i2_pre_post_processors

if __name__ == "__main__":
    from lerobot.scripts.lerobot_train import main
    main()
