# noisy_odom
This package adds a node to add drift to Odometry_msgs from simulation to create a loop closure dataset. Currently this code base does drift addition for a SE2 transformation. Adds error in (x, y, yaw).

# Installation Procedure
1. Clone the repo in the workspace.
```bash
git clone https://github.com/AnshShah3009/noisy_odom.git
```
2. Modify the topic and frame ids for tf and corrupt_odom topic publisher in the scripts/noisy_odom.py
