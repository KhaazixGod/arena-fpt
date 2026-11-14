#!/bin/bash
# P1 (paper-dev): diagnose the ORACLE ceiling on an UNLOCKED sheet (train_C2, objects of the train split), L0.5, n = 60.  No test_* cell, nothing frozen is touched.
source "$(dirname "$(readlink -f "$0")")/lib_chain.sh"
need_no_training
run_until p1_oracle_trainC2 runs/p1_oracle_train_c2_l05 60 --methods ORACLE --cells train_C2 --n 60 --arrangements-dir arrangements/sim --speeds L0.5
