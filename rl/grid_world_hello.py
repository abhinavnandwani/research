"""
Hello World for Reinforcement Learning
A simple grid world where an agent learns to reach a goal using Q-Learning
"""

import numpy as np
import random
from typing import Tuple

class GridWorld:
    """Simple 5x5 grid world environment"""

    def __init__(self, size=5):
        self.size = size
        self.agent_pos = [0, 0]  # Start at top-left
        self.goal_pos = [4, 4]   # Goal at bottom-right
        self.actions = ['up', 'down', 'left', 'right']

    def reset(self) -> Tuple[int, int]:
        """Reset agent to starting position"""
        self.agent_pos = [0, 0]
        return tuple(self.agent_pos)

    def step(self, action: str) -> Tuple[Tuple[int, int], float, bool]:
        """Take action and return (next_state, reward, done)"""
        # Move agent
        if action == 'up' and self.agent_pos[0] > 0:
            self.agent_pos[0] -= 1
        elif action == 'down' and self.agent_pos[0] < self.size - 1:
            self.agent_pos[0] += 1
        elif action == 'left' and self.agent_pos[1] > 0:
            self.agent_pos[1] -= 1
        elif action == 'right' and self.agent_pos[1] < self.size - 1:
            self.agent_pos[1] += 1

        # Check if goal reached
        done = (self.agent_pos == self.goal_pos)
        reward = 10.0 if done else -0.1  # Big reward at goal, small penalty for each step

        return tuple(self.agent_pos), reward, done


class QLearningAgent:
    """Q-Learning agent"""

    def __init__(self, actions, learning_rate=0.1, discount_factor=0.9, epsilon=0.1):
        self.actions = actions
        self.lr = learning_rate
        self.gamma = discount_factor
        self.epsilon = epsilon
        self.q_table = {}  # Q-table: {state: {action: value}}

    def get_q_value(self, state: Tuple[int, int], action: str) -> float:
        """Get Q-value for state-action pair"""
        if state not in self.q_table:
            self.q_table[state] = {a: 0.0 for a in self.actions}
        return self.q_table[state][action]

    def choose_action(self, state: Tuple[int, int]) -> str:
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon:
            return random.choice(self.actions)  # Explore
        else:
            # Exploit: choose best action
            q_values = {a: self.get_q_value(state, a) for a in self.actions}
            max_q = max(q_values.values())
            # Handle ties randomly
            best_actions = [a for a, q in q_values.items() if q == max_q]
            return random.choice(best_actions)

    def update(self, state: Tuple[int, int], action: str, reward: float,
               next_state: Tuple[int, int], done: bool):
        """Update Q-value using Q-learning update rule"""
        current_q = self.get_q_value(state, action)

        if done:
            target_q = reward
        else:
            # Q-learning: max over next state's Q-values
            next_q_values = [self.get_q_value(next_state, a) for a in self.actions]
            target_q = reward + self.gamma * max(next_q_values)

        # Q-learning update
        new_q = current_q + self.lr * (target_q - current_q)
        self.q_table[state][action] = new_q


def train(episodes=500, max_steps=100):
    """Train the agent"""
    env = GridWorld()
    agent = QLearningAgent(env.actions)

    episode_rewards = []

    print("Training Q-Learning Agent on Grid World...")
    print("=" * 50)

    for episode in range(episodes):
        state = env.reset()
        total_reward = 0

        for step in range(max_steps):
            # Choose and take action
            action = agent.choose_action(state)
            next_state, reward, done = env.step(action)

            # Update Q-values
            agent.update(state, action, reward, next_state, done)

            total_reward += reward
            state = next_state

            if done:
                break

        episode_rewards.append(total_reward)

        # Print progress
        if (episode + 1) % 100 == 0:
            avg_reward = np.mean(episode_rewards[-100:])
            print(f"Episode {episode + 1}/{episodes} | Avg Reward (last 100): {avg_reward:.2f}")

    return env, agent, episode_rewards


def test_agent(env, agent, num_episodes=10):
    """Test the trained agent"""
    print("\n" + "=" * 50)
    print("Testing Trained Agent...")
    print("=" * 50)

    for episode in range(num_episodes):
        state = env.reset()
        path = [state]
        total_reward = 0

        for step in range(20):  # Max 20 steps for testing
            # Greedy action selection (no exploration)
            q_values = {a: agent.get_q_value(state, a) for a in agent.actions}
            action = max(q_values, key=q_values.get)

            next_state, reward, done = env.step(action)
            path.append(next_state)
            total_reward += reward
            state = next_state

            if done:
                break

        print(f"Test Episode {episode + 1}: Steps={len(path)-1}, Reward={total_reward:.2f}")
        if episode == 0:  # Show first path
            print(f"  Path: {' -> '.join([str(p) for p in path])}")


def visualize_policy(agent, size=5):
    """Visualize the learned policy"""
    print("\n" + "=" * 50)
    print("Learned Policy (arrows show best action):")
    print("=" * 50)

    action_symbols = {'up': '↑', 'down': '↓', 'left': '←', 'right': '→'}

    for i in range(size):
        row = []
        for j in range(size):
            state = (i, j)
            if state == (4, 4):  # Goal
                row.append('G')
            else:
                q_values = {a: agent.get_q_value(state, a) for a in agent.actions}
                best_action = max(q_values, key=q_values.get)
                row.append(action_symbols[best_action])
        print(' '.join(row))


if __name__ == "__main__":
    print("\n🎮 Reinforcement Learning Hello World: Grid World with Q-Learning")
    print("=" * 70)
    print("The agent learns to navigate from top-left (0,0) to bottom-right (4,4)")
    print("=" * 70 + "\n")

    # Train the agent
    env, agent, rewards = train(episodes=500)

    # Test the trained agent
    test_agent(env, agent)

    # Visualize the learned policy
    visualize_policy(agent)

    print("\n" + "=" * 70)
    print("✓ Training complete! The agent learned to reach the goal efficiently.")
    print("=" * 70)
