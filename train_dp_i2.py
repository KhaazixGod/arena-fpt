"""Interface I2 for Diffusion Policy (paper-dev; KE_HOACH_PAPER.md P4): `lerobot-train` with --policy.type=diffusion and RELATIVE belt-frame actions.
Same arguments as lerobot-train; the data are the I2 datasets of to_lerobot_i2.py (stats already relative).  Like train_act_i2.py it only swaps the
policy's processor factory (arena/dp_i2.py: relative step that takes the last of the n_obs_steps states as the reference).  The DP model is unchanged.

    env -u PYTHONPATH ~/venvs/lerobot_data/bin/python train_dp_i2.py --policy.type=diffusion --dataset.repo_id=local/arena_so101_oraclew_i2 \
        --dataset.root=runs/p3_demos_w/lerobot_i2 --output_dir=runs/dp_w_s1000 --seed=1000 --policy.push_to_hub=false ...
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE]

import lerobot.policies.diffusion.processor_diffusion as processor_diffusion

from arena.dp_i2 import make_dp_i2_pre_post_processors

processor_diffusion.make_diffusion_pre_post_processors = make_dp_i2_pre_post_processors

if __name__ == "__main__":
    from lerobot.scripts.lerobot_train import main
    main()
