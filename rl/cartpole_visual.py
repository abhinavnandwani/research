"""
CartPole Balancing with Deep Q-Network (DQN)
Real-world classic control problem with neural network visualization
"""

import gymnasium as gym
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import torch
import torch.nn as nn
import torch.optim as optim
from collections import deque
import random

# Set seeds
np.random.seed(42)
torch.manual_seed(42)
random.seed(42)


class DQNNetwork(nn.Module):
    """Deep Q-Network for CartPole"""

    def __init__(self, state_dim=4, action_dim=2, hidden_dim=64):
        super(DQNNetwork, self).__init__()
        self.fc1 = nn.Linear(state_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, action_dim)

        # Store activations for visualization
        self.layer1_output = None
        self.layer2_output = None

    def forward(self, x):
        self.layer1_output = torch.relu(self.fc1(x))
        self.layer2_output = torch.relu(self.fc2(self.layer1_output))
        output = self.fc3(self.layer2_output)
        return output


class CartPoleDQNAgent:
    """DQN Agent for CartPole"""

    def __init__(self, state_dim=4, action_dim=2):
        self.state_dim = state_dim
        self.action_dim = action_dim

        self.policy_net = DQNNetwork(state_dim, action_dim)
        self.target_net = DQNNetwork(state_dim, action_dim)
        self.target_net.load_state_dict(self.policy_net.state_dict())

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.loss_fn = nn.MSELoss()

        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.batch_size = 64

        self.memory = deque(maxlen=10000)
        self.update_target_every = 10
        self.episode_count = 0

    def select_action(self, state, explore=True):
        """Select action using epsilon-greedy"""
        if explore and random.random() < self.epsilon:
            return random.randint(0, self.action_dim - 1)
        else:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax().item()

    def store_transition(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_step(self):
        if len(self.memory) < self.batch_size:
            return 0

        batch = random.sample(self.memory, self.batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)

        states = torch.FloatTensor(np.array(states))
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(np.array(next_states))
        dones = torch.FloatTensor(dones)

        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))

        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q

        loss = self.loss_fn(current_q.squeeze(), target_q)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        return loss.item()

    def update_target_network(self):
        self.target_net.load_state_dict(self.policy_net.state_dict())

    def decay_epsilon(self):
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)


class CartPoleVisualizer:
    """Advanced visualization for CartPole training"""

    def __init__(self):
        self.fig = plt.figure(figsize=(18, 10))
        self.fig.suptitle('CartPole Balancing - Deep Reinforcement Learning',
                         fontsize=16, fontweight='bold')

        # Create subplots
        gs = self.fig.add_gridspec(3, 4, hspace=0.35, wspace=0.35)

        # Main CartPole visualization
        self.ax_cart = self.fig.add_subplot(gs[0:2, 0:2])

        # Neural network visualization
        self.ax_network = self.fig.add_subplot(gs[0:2, 2:4])

        # Training metrics
        self.ax_reward = self.fig.add_subplot(gs[2, 0])
        self.ax_steps = self.fig.add_subplot(gs[2, 1])
        self.ax_loss = self.fig.add_subplot(gs[2, 2])
        self.ax_epsilon = self.fig.add_subplot(gs[2, 3])

        # Data storage
        self.episode_rewards = []
        self.episode_steps = []
        self.losses = []
        self.epsilons = []

    def draw_cartpole(self, state, episode, total_steps, reward):
        """Draw CartPole state"""
        self.ax_cart.clear()

        # Extract state variables
        x, x_dot, theta, theta_dot = state

        # Cart dimensions
        cart_width = 0.5
        cart_height = 0.3
        pole_length = 1.0
        pole_width = 0.05

        # Draw track
        self.ax_cart.plot([-2.4, 2.4], [0, 0], 'k-', linewidth=3)
        self.ax_cart.plot([-2.4, -2.4], [-0.05, 0.05], 'k-', linewidth=3)
        self.ax_cart.plot([2.4, 2.4], [-0.05, 0.05], 'k-', linewidth=3)

        # Draw cart
        cart_x = x
        cart_y = 0
        cart = FancyBboxPatch(
            (cart_x - cart_width/2, cart_y),
            cart_width, cart_height,
            boxstyle="round,pad=0.05",
            facecolor='dodgerblue',
            edgecolor='darkblue',
            linewidth=3
        )
        self.ax_cart.add_patch(cart)

        # Draw wheels
        wheel_radius = 0.08
        for wheel_x in [cart_x - cart_width/3, cart_x + cart_width/3]:
            wheel = Circle((wheel_x, wheel_radius), wheel_radius,
                          facecolor='black', edgecolor='gray', linewidth=2)
            self.ax_cart.add_patch(wheel)

        # Draw pole
        pole_end_x = cart_x + pole_length * np.sin(theta)
        pole_end_y = cart_y + cart_height + pole_length * np.cos(theta)

        # Pole body
        pole_coords = [
            [cart_x - pole_width/2, cart_y + cart_height],
            [cart_x + pole_width/2, cart_y + cart_height],
            [pole_end_x + pole_width/2, pole_end_y],
            [pole_end_x - pole_width/2, pole_end_y]
        ]

        pole_color = 'green' if abs(theta) < 0.2 else 'orange' if abs(theta) < 0.3 else 'red'
        pole = patches.Polygon(pole_coords, facecolor=pole_color,
                              edgecolor='darkgreen', linewidth=2, alpha=0.8)
        self.ax_cart.add_patch(pole)

        # Draw pole joint
        joint = Circle((cart_x, cart_y + cart_height), 0.08,
                      facecolor='gold', edgecolor='darkorange', linewidth=2, zorder=10)
        self.ax_cart.add_patch(joint)

        # Draw pole tip
        tip = Circle((pole_end_x, pole_end_y), 0.1,
                    facecolor='red', edgecolor='darkred', linewidth=2, zorder=10)
        self.ax_cart.add_patch(tip)

        # Settings
        self.ax_cart.set_xlim(-3, 3)
        self.ax_cart.set_ylim(-0.5, 2)
        self.ax_cart.set_aspect('equal')
        self.ax_cart.grid(True, alpha=0.3)
        self.ax_cart.set_xlabel('Position', fontsize=11)
        self.ax_cart.set_ylabel('Height', fontsize=11)

        # Status info
        status_text = f'Episode: {episode} | Steps: {total_steps} | Reward: {reward:.0f}\n'
        status_text += f'Cart Pos: {x:.2f} | Angle: {theta:.2f} rad ({np.degrees(theta):.1f}°)'
        self.ax_cart.set_title(status_text, fontsize=10, fontweight='bold')

    def draw_neural_network(self, agent, state):
        """Visualize neural network with activations"""
        self.ax_network.clear()

        # Get network activations
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = agent.policy_net(state_tensor)
            layer1_act = agent.policy_net.layer1_output[0].numpy()
            layer2_act = agent.policy_net.layer2_output[0].numpy()
            output_act = q_values[0].numpy()

        # Network architecture
        layers = [
            ('Input', 4, state),
            ('Hidden 1', 64, layer1_act),
            ('Hidden 2', 64, layer2_act),
            ('Output', 2, output_act)
        ]

        # Draw network
        layer_x_positions = [0, 0.3, 0.6, 0.9]
        max_neurons_display = 12

        for i, (layer_name, n_neurons, activations) in enumerate(layers):
            x_pos = layer_x_positions[i]

            # Display subset of neurons for hidden layers
            display_neurons = min(n_neurons, max_neurons_display)
            y_positions = np.linspace(0.1, 0.9, display_neurons)

            for j, y_pos in enumerate(y_positions):
                # Get activation value
                if j < len(activations):
                    activation = activations[j]
                    # Normalize for color
                    norm_activation = (activation - activations.min()) / (activations.max() - activations.min() + 1e-8)
                else:
                    norm_activation = 0

                # Draw neuron
                color = plt.cm.RdYlGn(norm_activation)
                neuron = Circle((x_pos, y_pos), 0.03,
                              facecolor=color, edgecolor='black', linewidth=1.5, zorder=5)
                self.ax_network.add_patch(neuron)

                # Add activation value for input and output
                if i == 0:  # Input layer
                    labels = ['x', 'v', 'θ', 'ω']
                    self.ax_network.text(x_pos - 0.08, y_pos, f'{labels[j]}',
                                        fontsize=8, ha='right', va='center')
                    self.ax_network.text(x_pos + 0.05, y_pos, f'{activation:.2f}',
                                        fontsize=7, ha='left', va='center')
                elif i == 3:  # Output layer
                    actions = ['Left', 'Right']
                    self.ax_network.text(x_pos + 0.05, y_pos, f'{actions[j]}\nQ={activation:.2f}',
                                        fontsize=8, ha='left', va='center',
                                        fontweight='bold' if activation == output_act.max() else 'normal')

            # Layer label
            self.ax_network.text(x_pos, -0.05, layer_name,
                               fontsize=9, ha='center', fontweight='bold')

        # Draw connections (simplified - just show some connections)
        for i in range(len(layers) - 1):
            x_start = layer_x_positions[i]
            x_end = layer_x_positions[i + 1]

            n_start = min(layers[i][1], max_neurons_display)
            n_end = min(layers[i + 1][1], max_neurons_display)

            y_start_positions = np.linspace(0.1, 0.9, n_start)
            y_end_positions = np.linspace(0.1, 0.9, n_end)

            # Draw subset of connections
            for y_s in y_start_positions[::3]:  # Every 3rd neuron
                for y_e in y_end_positions[::3]:
                    self.ax_network.plot([x_start + 0.03, x_end - 0.03],
                                        [y_s, y_e],
                                        'gray', alpha=0.1, linewidth=0.5, zorder=1)

        self.ax_network.set_xlim(-0.15, 1.1)
        self.ax_network.set_ylim(-0.1, 1)
        self.ax_network.axis('off')
        self.ax_network.set_title('Neural Network (DQN) Activations', fontsize=11, fontweight='bold')

    def update_metrics(self, episode_reward, episode_steps, loss, epsilon):
        """Update training metrics plots"""
        self.episode_rewards.append(episode_reward)
        self.episode_steps.append(episode_steps)
        self.losses.append(loss if loss > 0 else 0)
        self.epsilons.append(epsilon)

        # Plot episode rewards
        self.ax_reward.clear()
        self.ax_reward.plot(self.episode_rewards, 'b-', alpha=0.5, linewidth=1)
        if len(self.episode_rewards) >= 10:
            smoothed = np.convolve(self.episode_rewards, np.ones(10)/10, mode='valid')
            self.ax_reward.plot(range(9, len(self.episode_rewards)), smoothed,
                               'darkblue', linewidth=2, label='Avg(10)')
            self.ax_reward.legend(fontsize=8)
        self.ax_reward.axhline(y=195, color='g', linestyle='--', alpha=0.5, label='Solved')
        self.ax_reward.set_xlabel('Episode', fontsize=9)
        self.ax_reward.set_ylabel('Reward', fontsize=9)
        self.ax_reward.set_title('Episode Rewards', fontsize=10, fontweight='bold')
        self.ax_reward.grid(True, alpha=0.3)

        # Plot episode steps
        self.ax_steps.clear()
        self.ax_steps.plot(self.episode_steps, 'g-', alpha=0.5, linewidth=1)
        if len(self.episode_steps) >= 10:
            smoothed = np.convolve(self.episode_steps, np.ones(10)/10, mode='valid')
            self.ax_steps.plot(range(9, len(self.episode_steps)), smoothed,
                              'darkgreen', linewidth=2, label='Avg(10)')
            self.ax_steps.legend(fontsize=8)
        self.ax_steps.set_xlabel('Episode', fontsize=9)
        self.ax_steps.set_ylabel('Steps', fontsize=9)
        self.ax_steps.set_title('Episode Duration', fontsize=10, fontweight='bold')
        self.ax_steps.grid(True, alpha=0.3)

        # Plot loss
        self.ax_loss.clear()
        if len(self.losses) > 0:
            self.ax_loss.plot(self.losses, 'r-', alpha=0.5, linewidth=1)
            if len(self.losses) >= 50:
                smoothed = np.convolve(self.losses, np.ones(50)/50, mode='valid')
                self.ax_loss.plot(range(49, len(self.losses)), smoothed,
                                 'darkred', linewidth=2, label='Avg(50)')
                self.ax_loss.legend(fontsize=8)
        self.ax_loss.set_xlabel('Episode', fontsize=9)
        self.ax_loss.set_ylabel('Loss', fontsize=9)
        self.ax_loss.set_title('Training Loss', fontsize=10, fontweight='bold')
        self.ax_loss.grid(True, alpha=0.3)

        # Plot epsilon
        self.ax_epsilon.clear()
        self.ax_epsilon.plot(self.epsilons, 'purple', linewidth=2)
        self.ax_epsilon.set_xlabel('Episode', fontsize=9)
        self.ax_epsilon.set_ylabel('Epsilon', fontsize=9)
        self.ax_epsilon.set_title('Exploration Rate', fontsize=10, fontweight='bold')
        self.ax_epsilon.set_ylim([0, 1.1])
        self.ax_epsilon.grid(True, alpha=0.3)


def train_cartpole(num_episodes=300, render_interval=5):
    """Train CartPole with visualization"""

    # Create environment
    env = gym.make('CartPole-v1')
    agent = CartPoleDQNAgent()
    viz = CartPoleVisualizer()

    plt.ion()
    plt.show()

    print("\n" + "="*80)
    print("CARTPOLE BALANCING - DEEP Q-NETWORK (DQN)")
    print("="*80)
    print("Objective: Keep the pole balanced for as long as possible")
    print("Solved: Average reward > 195 over 100 consecutive episodes")
    print("="*80 + "\n")

    solved = False

    for episode in range(num_episodes):
        state, _ = env.reset()
        total_reward = 0
        done = False
        steps = 0
        episode_loss = 0

        while not done:
            # Select action
            action = agent.select_action(state)

            # Take action
            next_state, reward, terminated, truncated, _ = env.step(action)
            done = terminated or truncated

            # Store transition
            agent.store_transition(state, action, reward, next_state, done)

            # Train
            loss = agent.train_step()
            if loss > 0:
                episode_loss = loss

            total_reward += reward
            steps += 1
            state = next_state

            # Visualize periodically
            if episode % render_interval == 0 and steps % 5 == 0:
                viz.draw_cartpole(state, episode + 1, steps, total_reward)
                viz.draw_neural_network(agent, state)
                plt.pause(0.001)

        # End of episode
        viz.draw_cartpole(state, episode + 1, steps, total_reward)
        viz.draw_neural_network(agent, state)
        viz.update_metrics(total_reward, steps, episode_loss, agent.epsilon)
        plt.pause(0.01)

        # Update networks
        if episode % agent.update_target_every == 0:
            agent.update_target_network()

        agent.decay_epsilon()

        # Check if solved
        if len(viz.episode_rewards) >= 100:
            avg_reward = np.mean(viz.episode_rewards[-100:])
            if avg_reward >= 195 and not solved:
                print(f"\n{'='*80}")
                print(f"SOLVED in {episode + 1} episodes! Average reward: {avg_reward:.1f}")
                print(f"{'='*80}\n")
                solved = True

        # Print progress
        status = "SOLVED! " if solved else ""
        print(f"{status}Episode {episode + 1:3d} | Steps: {steps:3d} | "
              f"Reward: {total_reward:6.1f} | Loss: {episode_loss:6.4f} | "
              f"Epsilon: {agent.epsilon:.3f}")

    env.close()

    print("\n" + "="*80)
    print("TRAINING COMPLETE!")
    print("="*80)
    print(f"Final Average Reward (last 100): {np.mean(viz.episode_rewards[-100:]):.1f}")
    print(f"Final Average Steps (last 100): {np.mean(viz.episode_steps[-100:]):.1f}")
    print("="*80)

    plt.ioff()
    plt.show()

    return agent, viz


if __name__ == "__main__":
    agent, viz = train_cartpole(num_episodes=300, render_interval=3)
