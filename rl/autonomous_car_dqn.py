"""
Autonomous Car Learning to Navigate Traffic using Deep Q-Learning (DQN)
A visually sophisticated demonstration of reinforcement learning in action
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from collections import deque
import random
from typing import Tuple, List
import torch
import torch.nn as nn
import torch.optim as optim

# Set random seeds for reproducibility
np.random.seed(42)
torch.manual_seed(42)
random.seed(42)


class Highway:
    """Highway environment with multiple lanes and traffic"""

    def __init__(self, num_lanes=3, road_length=100):
        self.num_lanes = num_lanes
        self.road_length = road_length
        self.lane_width = 4.0

        # Agent car properties
        self.agent_pos = [0, self.num_lanes // 2]  # [x, lane]
        self.agent_speed = 1.0
        self.agent_max_speed = 2.0
        self.agent_min_speed = 0.5

        # Traffic cars: [x, lane, speed]
        self.traffic_cars = []
        self.max_traffic = 8
        self.spawn_probability = 0.3

        # Rewards
        self.collision_penalty = -100
        self.goal_reward = 100
        self.step_reward = 1  # Reward for moving forward
        self.lane_change_penalty = -0.5

        # Episode tracking
        self.steps = 0
        self.max_steps = 500
        self.distance_traveled = 0

    def reset(self) -> np.ndarray:
        """Reset environment"""
        self.agent_pos = [0, self.num_lanes // 2]
        self.agent_speed = 1.0
        self.traffic_cars = []
        self.steps = 0
        self.distance_traveled = 0

        # Spawn initial traffic
        for _ in range(4):
            self._spawn_traffic()

        return self._get_state()

    def _spawn_traffic(self):
        """Spawn a new traffic car"""
        if len(self.traffic_cars) < self.max_traffic and random.random() < self.spawn_probability:
            lane = random.randint(0, self.num_lanes - 1)
            # Spawn ahead of agent
            x = self.agent_pos[0] + random.uniform(10, 40)
            speed = random.uniform(0.3, 1.5)
            self.traffic_cars.append([x, lane, speed])

    def _get_state(self) -> np.ndarray:
        """
        Get state representation:
        - Agent lane (one-hot encoded)
        - Agent speed (normalized)
        - Distances to nearest cars in each lane (normalized)
        - Speeds of nearest cars in each lane (normalized)
        """
        state = np.zeros(2 + 2 * self.num_lanes)

        # Agent lane (one-hot)
        agent_lane = int(self.agent_pos[1])
        if 0 <= agent_lane < self.num_lanes:
            state[agent_lane] = 1.0

        # Agent speed (normalized)
        state[self.num_lanes] = self.agent_speed / self.agent_max_speed

        # Find nearest car in each lane
        for lane in range(self.num_lanes):
            min_dist = float('inf')
            nearest_speed = 0

            for car in self.traffic_cars:
                if int(car[1]) == lane and car[0] > self.agent_pos[0]:
                    dist = car[0] - self.agent_pos[0]
                    if dist < min_dist:
                        min_dist = dist
                        nearest_speed = car[2]

            # Normalize distance (closer = higher value)
            if min_dist < float('inf'):
                state[self.num_lanes + 1 + lane] = max(0, 1 - min_dist / 30.0)
                state[self.num_lanes + 1 + self.num_lanes + lane] = nearest_speed / self.agent_max_speed

        return state

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, dict]:
        """
        Take action:
        0: Maintain lane, maintain speed
        1: Change lane left
        2: Change lane right
        3: Accelerate
        4: Decelerate
        """
        self.steps += 1
        reward = 0
        lane_changed = False

        # Execute action
        if action == 1 and self.agent_pos[1] > 0:  # Left
            self.agent_pos[1] -= 1
            reward += self.lane_change_penalty
            lane_changed = True
        elif action == 2 and self.agent_pos[1] < self.num_lanes - 1:  # Right
            self.agent_pos[1] += 1
            reward += self.lane_change_penalty
            lane_changed = True
        elif action == 3:  # Accelerate
            self.agent_speed = min(self.agent_max_speed, self.agent_speed + 0.2)
        elif action == 4:  # Decelerate
            self.agent_speed = max(self.agent_min_speed, self.agent_speed - 0.2)

        # Move agent forward
        self.agent_pos[0] += self.agent_speed
        self.distance_traveled += self.agent_speed

        # Update traffic
        for car in self.traffic_cars:
            car[0] += car[2]

        # Remove cars that are behind
        self.traffic_cars = [car for car in self.traffic_cars if car[0] > self.agent_pos[0] - 20]

        # Spawn new traffic
        self._spawn_traffic()

        # Check collision
        collision = False
        for car in self.traffic_cars:
            if abs(car[0] - self.agent_pos[0]) < 3 and int(car[1]) == int(self.agent_pos[1]):
                collision = True
                break

        # Calculate reward
        if collision:
            reward += self.collision_penalty
            done = True
        elif self.steps >= self.max_steps:
            reward += self.goal_reward + self.distance_traveled * 0.5
            done = True
        else:
            # Reward for moving forward
            reward += self.step_reward
            done = False

        next_state = self._get_state()
        info = {
            'distance': self.distance_traveled,
            'collision': collision,
            'lane_changed': lane_changed
        }

        return next_state, reward, done, info


class DQN(nn.Module):
    """Deep Q-Network"""

    def __init__(self, state_dim: int, action_dim: int):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )

    def forward(self, x):
        return self.network(x)


class DQNAgent:
    """Deep Q-Learning Agent with Experience Replay"""

    def __init__(self, state_dim: int, action_dim: int, lr=0.001):
        self.state_dim = state_dim
        self.action_dim = action_dim

        # Q-Networks
        self.policy_net = DQN(state_dim, action_dim)
        self.target_net = DQN(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.loss_fn = nn.MSELoss()

        # Hyperparameters
        self.gamma = 0.99  # Discount factor
        self.epsilon = 1.0  # Exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 64
        self.target_update_freq = 10

        # Experience replay
        self.memory = deque(maxlen=10000)

        # Tracking
        self.episode_count = 0

    def select_action(self, state: np.ndarray) -> int:
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax().item()

    def store_transition(self, state, action, reward, next_state, done):
        """Store experience in replay buffer"""
        self.memory.append((state, action, reward, next_state, done))

    def train(self):
        """Train the network using experience replay"""
        if len(self.memory) < self.batch_size:
            return 0

        # Sample batch
        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)

        # Current Q values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))

        # Target Q values
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q

        # Compute loss
        loss = self.loss_fn(current_q.squeeze(), target_q)

        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def update_target_network(self):
        """Update target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        """Decay exploration rate"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


class VisualizationDashboard:
    """Real-time visualization dashboard"""

    def __init__(self):
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle('Autonomous Car Learning with Deep Q-Network (DQN)',
                         fontsize=16, fontweight='bold')

        # Create subplots
        gs = self.fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        self.ax_road = self.fig.add_subplot(gs[0:2, :])  # Highway view
        self.ax_reward = self.fig.add_subplot(gs[2, 0])  # Episode rewards
        self.ax_distance = self.fig.add_subplot(gs[2, 1])  # Distance traveled
        self.ax_epsilon = self.fig.add_subplot(gs[2, 2])  # Epsilon decay

        # Data storage
        self.episode_rewards = []
        self.episode_distances = []
        self.episode_epsilons = []
        self.losses = []

    def draw_highway(self, env: Highway, episode: int, total_reward: float):
        """Draw the highway with cars"""
        self.ax_road.clear()

        # Set up highway view
        view_distance = 50
        x_min = env.agent_pos[0] - 10
        x_max = env.agent_pos[0] + view_distance

        self.ax_road.set_xlim(x_min, x_max)
        self.ax_road.set_ylim(-1, env.num_lanes * env.lane_width + 1)

        # Draw lanes
        for i in range(env.num_lanes + 1):
            y = i * env.lane_width
            self.ax_road.plot([x_min, x_max], [y, y], 'k--', alpha=0.3, linewidth=1)

        # Draw lane markers
        for i in range(env.num_lanes):
            y = (i + 0.5) * env.lane_width
            for x in range(int(x_min), int(x_max), 5):
                self.ax_road.plot([x, x + 2], [y, y], 'w-', linewidth=2)

        # Draw road background
        self.ax_road.add_patch(patches.Rectangle(
            (x_min, 0), x_max - x_min, env.num_lanes * env.lane_width,
            facecolor='gray', alpha=0.3, zorder=0
        ))

        # Draw traffic cars
        for car in env.traffic_cars:
            if x_min <= car[0] <= x_max:
                y_center = car[1] * env.lane_width + env.lane_width / 2
                car_rect = patches.Rectangle(
                    (car[0] - 2, y_center - 1),
                    4, 2,
                    facecolor='red', edgecolor='darkred', linewidth=2, zorder=2
                )
                self.ax_road.add_patch(car_rect)

        # Draw agent car (green)
        y_center = env.agent_pos[1] * env.lane_width + env.lane_width / 2
        agent_rect = patches.Rectangle(
            (env.agent_pos[0] - 2, y_center - 1),
            4, 2,
            facecolor='lime', edgecolor='darkgreen', linewidth=3, zorder=3
        ))
        self.ax_road.add_patch(agent_rect)

        # Add arrow to show direction
        self.ax_road.arrow(env.agent_pos[0], y_center, 3, 0,
                          head_width=0.8, head_length=1, fc='darkgreen', ec='darkgreen', zorder=4)

        # Labels
        self.ax_road.set_xlabel('Distance (m)', fontsize=12)
        self.ax_road.set_ylabel('Lane', fontsize=12)
        self.ax_road.set_title(
            f'Episode {episode} | Distance: {env.distance_traveled:.1f}m | Reward: {total_reward:.1f} | Speed: {env.agent_speed:.1f}m/s',
            fontsize=12, fontweight='bold'
        )
        self.ax_road.grid(True, alpha=0.2)

    def update_metrics(self, episode_reward: float, distance: float, epsilon: float):
        """Update training metrics"""
        self.episode_rewards.append(episode_reward)
        self.episode_distances.append(distance)
        self.episode_epsilons.append(epsilon)

        # Plot rewards
        self.ax_reward.clear()
        self.ax_reward.plot(self.episode_rewards, color='blue', alpha=0.6, linewidth=1)
        if len(self.episode_rewards) >= 10:
            smoothed = np.convolve(self.episode_rewards, np.ones(10)/10, mode='valid')
            self.ax_reward.plot(range(9, len(self.episode_rewards)), smoothed,
                               color='darkblue', linewidth=2, label='Moving Avg (10)')
            self.ax_reward.legend()
        self.ax_reward.set_xlabel('Episode')
        self.ax_reward.set_ylabel('Total Reward')
        self.ax_reward.set_title('Episode Rewards')
        self.ax_reward.grid(True, alpha=0.3)

        # Plot distances
        self.ax_distance.clear()
        self.ax_distance.plot(self.episode_distances, color='green', alpha=0.6, linewidth=1)
        if len(self.episode_distances) >= 10:
            smoothed = np.convolve(self.episode_distances, np.ones(10)/10, mode='valid')
            self.ax_distance.plot(range(9, len(self.episode_distances)), smoothed,
                                 color='darkgreen', linewidth=2, label='Moving Avg (10)')
            self.ax_distance.legend()
        self.ax_distance.set_xlabel('Episode')
        self.ax_distance.set_ylabel('Distance (m)')
        self.ax_distance.set_title('Distance Traveled')
        self.ax_distance.grid(True, alpha=0.3)

        # Plot epsilon
        self.ax_epsilon.clear()
        self.ax_epsilon.plot(self.episode_epsilons, color='purple', linewidth=2)
        self.ax_epsilon.set_xlabel('Episode')
        self.ax_epsilon.set_ylabel('Epsilon')
        self.ax_epsilon.set_title('Exploration Rate')
        self.ax_epsilon.grid(True, alpha=0.3)
        self.ax_epsilon.set_ylim([0, 1.1])


def train_autonomous_car(num_episodes=200, render_interval=5):
    """Train the autonomous car with live visualization"""

    # Initialize environment and agent
    env = Highway(num_lanes=3)
    state_dim = 2 + 2 * env.num_lanes  # State dimension
    action_dim = 5  # 5 actions
    agent = DQNAgent(state_dim, action_dim)

    # Visualization
    dashboard = VisualizationDashboard()
    plt.ion()
    plt.show()

    print("\n" + "="*80)
    print("AUTONOMOUS CAR TRAINING WITH DEEP Q-NETWORK (DQN)")
    print("="*80)
    print(f"State Dimension: {state_dim}")
    print(f"Action Space: {action_dim} (Maintain, Left, Right, Accelerate, Decelerate)")
    print(f"Training Episodes: {num_episodes}")
    print("="*80 + "\n")

    for episode in range(num_episodes):
        state = env.reset()
        total_reward = 0
        done = False
        step_count = 0

        while not done:
            # Select and perform action
            action = agent.select_action(state)
            next_state, reward, done, info = env.step(action)

            # Store transition
            agent.store_transition(state, action, reward, next_state, done)

            # Train agent
            loss = agent.train()

            total_reward += reward
            state = next_state
            step_count += 1

            # Render occasionally
            if episode % render_interval == 0 and step_count % 10 == 0:
                dashboard.draw_highway(env, episode + 1, total_reward)
                plt.pause(0.01)

        # Update target network periodically
        if episode % agent.target_update_freq == 0:
            agent.update_target_network()

        # Decay epsilon
        agent.decay_epsilon()

        # Update metrics
        dashboard.update_metrics(total_reward, info['distance'], agent.epsilon)
        dashboard.draw_highway(env, episode + 1, total_reward)
        plt.pause(0.01)

        # Print progress
        collision_str = "COLLISION" if info['collision'] else "SUCCESS"
        print(f"Episode {episode + 1:3d} | Reward: {total_reward:7.1f} | "
              f"Distance: {info['distance']:6.1f}m | Steps: {step_count:3d} | "
              f"Epsilon: {agent.epsilon:.3f} | {collision_str}")

    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print(f"Final Average Reward (last 20): {np.mean(dashboard.episode_rewards[-20:]):.1f}")
    print(f"Final Average Distance (last 20): {np.mean(dashboard.episode_distances[-20:]):.1f}m")
    print("="*80)

    plt.ioff()
    plt.show()

    return env, agent, dashboard


if __name__ == "__main__":
    env, agent, dashboard = train_autonomous_car(num_episodes=200, render_interval=3)
