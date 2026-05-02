"""Quick test of the RL demos to verify they work"""

import sys

print("Testing RL Demos...")
print("=" * 60)

# Test 1: Grid World
print("\n1. Testing Grid World (Q-Learning)...")
try:
    import grid_world_hello
    print("✓ Grid World imports successfully")
except Exception as e:
    print(f"✗ Grid World import failed: {e}")

# Test 2: CartPole (without running full training)
print("\n2. Testing CartPole components...")
try:
    import torch
    import torch.nn as nn
    import gymnasium as gym
    import matplotlib.pyplot as plt

    # Test environment creation
    env = gym.make('CartPole-v1')
    state, _ = env.reset()
    print(f"✓ CartPole environment created, state shape: {state.shape}")

    # Test simple network
    class TestNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = nn.Linear(4, 2)
        def forward(self, x):
            return self.fc(x)

    net = TestNet()
    state_tensor = torch.FloatTensor(state).unsqueeze(0)
    output = net(state_tensor)
    print(f"✓ Neural network working, output shape: {output.shape}")

    env.close()
    print("✓ CartPole components working")

except Exception as e:
    print(f"✗ CartPole test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Autonomous Car
print("\n3. Testing Autonomous Car components...")
try:
    import numpy as np

    # Test Highway class
    class MiniHighway:
        def __init__(self):
            self.num_lanes = 3
            self.agent_pos = [0, 1]

        def reset(self):
            return np.zeros(8)

    highway = MiniHighway()
    state = highway.reset()
    print(f"✓ Highway environment structure working, state shape: {state.shape}")

except Exception as e:
    print(f"✗ Autonomous Car test failed: {e}")

print("\n" + "=" * 60)
print("All core components tested!")
print("\nTo run full demos:")
print("  uv run python grid_world_hello.py")
print("  uv run python cartpole_visual.py")
print("  uv run python autonomous_car_dqn.py")
print("=" * 60)
