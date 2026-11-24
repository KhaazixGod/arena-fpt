# fptros: ROS 2 transport of the policy (thesis Sections 3.2 and 6.5)

Two processes talk through standard ROS 2 messages (ROS 2 Jazzy, Fast DDS, reliable QoS, same host):

* `fptros.policy_node` (policy side, LeRobot venv): wraps any method of the arena (DP_W1, M4 v2 ...). Subscribes `/camera/image_raw`, `/joint_states`, `/belt/counter`, `/fpt/tick`;
  publishes `/robot/command` and `/fpt/status`.
* `fptros.client` (arena side, Isaac venv): the method `fptros.client:make_method`; it publishes what the simulated robot has and waits for the command (lockstep: simulation time does not move
  while the policy computes). `--method-arg ros2_delay_ticks=N` applies every command N control ticks late (20 ms each), exactly, in virtual time.

Run:

    source /opt/ros/jazzy/setup.bash
    DP_CKPT=runs/dp_w_s1000/checkpoints/last/pretrained_model env -u PYTHONPATH PYTHONPATH=.:../cl0:$PYTHONPATH ~/venvs/lerobot_data/bin/python -m fptros.policy_node \
        --factory diffusion_vs2:make_method --path m4v2 --path m4 --path . --path ../cl0
    # in another shell, the arena:
    source /opt/ros/jazzy/setup.bash; PYTHONPATH=.:../cl0:$PYTHONPATH ~/env_isaac/bin/python -m arena.run_arena --methods fptros.client:make_method --cells dev_C2 --speeds L0.5 --n 20 --objects sim --out runs/ros2_dev

`fptros.mock_arena` feeds recorded frames to a dummy method for a transport-only test (no Isaac, no GPU).
Not done: a free-running (real-time, not lockstep) loop with the Isaac ROS 2 bridge, and a real robot.
