# Reinforcement Learning - Visual Demonstrations

Welcome to an interactive journey into **Reinforcement Learning**! This collection features visually sophisticated demonstrations of real-world RL applications.

## 🎯 What's Inside

### 1. Grid World (Basic) - `grid_world_hello.py`
A simple Q-learning example where an agent learns to navigate a 5×5 grid.
- **Algorithm**: Tabular Q-Learning
- **Goal**: Navigate from top-left to bottom-right
- **Visualization**: ASCII policy map

**Run it:**
```bash
uv run python grid_world_hello.py
```

---

### 2. Autonomous Car (Advanced) - `autonomous_car_dqn.py`
A self-driving car learning to navigate highway traffic using Deep Q-Networks.

**Features:**
- 🚗 **Realistic Highway Environment**: 3-lane highway with dynamic traffic
- 🧠 **Deep Q-Network (DQN)**: Neural network for value function approximation
- 🎨 **Live Visualization Dashboard**:
  - Real-time highway view with cars
  - Episode reward tracking
  - Distance traveled metrics
  - Exploration rate (epsilon) decay
- 🎮 **Actions**: Lane changes, acceleration, deceleration
- 📊 **Experience Replay**: Efficient learning from past experiences

**Key RL Concepts:**
- State representation: Lane position, speed, proximity to traffic
- Reward shaping: Collision penalties, forward progress rewards
- Experience replay buffer
- Target network for stability
- Epsilon-greedy exploration

**Run it:**
```bash
uv run python autonomous_car_dqn.py
```

**What You'll See:**
- Green car (your agent) learning to navigate
- Red cars (traffic obstacles)
- Real-time metrics showing learning progress
- Agent improving from random behavior to skilled navigation

---

### 3. CartPole Balancing (Classic) - `cartpole_visual.py`
The classic inverted pendulum problem - keep a pole balanced on a moving cart.

**Features:**
- 🎪 **Physics Simulation**: Using OpenAI Gymnasium
- 🧠 **Deep Q-Network**: 4-64-64-2 neural architecture
- 🎨 **Advanced Visualizations**:
  - Real-time CartPole physics rendering
  - **Neural network activation visualization**: See the network "think"!
  - Training loss curves
  - Episode duration tracking
  - Exploration rate monitoring
- ✅ **Solved Threshold**: Average reward > 195 over 100 episodes

**Neural Network Architecture:**
```
Input (4) → Hidden (64) → Hidden (64) → Output (2)
  [x, v, θ, ω]    [ReLU]     [ReLU]    [Left, Right]
```

**Key Highlights:**
- Watch network activations light up in real-time
- See Q-values for each action
- Color-coded pole (green=good, red=danger)
- Smooth learning curves with moving averages

**Run it:**
```bash
uv run python cartpole_visual.py
```

**Training Progress:**
- Episodes 0-50: Random exploration, frequent failures
- Episodes 50-150: Learning stabilization strategies
- Episodes 150+: Consistent balancing, approaching "solved" status

---

## 🚀 Quick Start

### Installation
```bash
cd rl
uv sync  # Install all dependencies
```

### Dependencies
- **NumPy**: Numerical computations
- **PyTorch**: Deep learning framework
- **Matplotlib**: Visualizations and plots
- **Gymnasium**: RL environments (CartPole)
- **OpenCV & Pillow**: Image processing

---

## 📚 RL Concepts Explained

### What is Reinforcement Learning?
An agent learns to make decisions by interacting with an environment:
1. **Observe** the current state
2. **Take** an action
3. **Receive** a reward
4. **Learn** to maximize long-term rewards

### Key Algorithms Demonstrated

#### Q-Learning (Grid World)
- **Tabular method**: Stores Q-values in a table
- **Update rule**: `Q(s,a) ← Q(s,a) + α[r + γ·max Q(s',a') - Q(s,a)]`
- **Best for**: Small, discrete state spaces

#### Deep Q-Network - DQN (Car & CartPole)
- **Function approximation**: Neural network estimates Q-values
- **Experience replay**: Learn from past experiences
- **Target network**: Stabilizes training
- **Best for**: Large or continuous state spaces

### Training Components

1. **Epsilon-Greedy Exploration**
   - Start with high epsilon (random actions)
   - Gradually decrease (exploit learned policy)
   - Balance exploration vs exploitation

2. **Reward Shaping**
   - Design rewards to guide learning
   - Avoid sparse rewards
   - Penalize bad behaviors, reward good ones

3. **Neural Network Updates**
   - Batch learning from replay buffer
   - Target network for stable Q-value targets
   - Adam optimizer for efficient gradient descent

---

## 🎓 Learning Path

1. **Start with Grid World**: Understand basic Q-learning
2. **Move to CartPole**: See deep learning in action with neural network visualization
3. **Try Autonomous Car**: Apply to a complex, multi-faceted problem

---

## 🎨 Visualization Features

### Real-Time Dashboards
- **Live environment rendering**: See the agent in action
- **Training metrics**: Rewards, losses, epsilon decay
- **Moving averages**: Smooth out noisy training signals
- **Color-coded indicators**: Quick visual feedback

### Neural Network Visualization (CartPole)
- **Layer activations**: See which neurons fire
- **Connection weights**: Visual representation of network structure
- **Q-value outputs**: Understand action selection
- **Color mapping**: Activation intensity visualization

---

## 🔧 Customization

### Modify Hyperparameters

**Learning Rate:**
```python
agent = DQNAgent(state_dim, action_dim, lr=0.001)  # Default
agent = DQNAgent(state_dim, action_dim, lr=0.01)   # Faster learning
```

**Exploration Rate:**
```python
agent.epsilon = 1.0         # Initial exploration
agent.epsilon_decay = 0.995 # Decay rate
agent.epsilon_min = 0.01    # Minimum exploration
```

**Network Architecture:**
```python
# In DQNNetwork class
self.fc1 = nn.Linear(state_dim, 128)  # Larger network
self.fc2 = nn.Linear(128, 128)
self.fc3 = nn.Linear(128, action_dim)
```

### Adjust Visualization Speed
```python
# Render less frequently for faster training
train_autonomous_car(num_episodes=200, render_interval=10)

# Render more frequently for detailed observation
train_cartpole(num_episodes=300, render_interval=1)
```

---

## 📊 Expected Results

### Grid World
- **Episodes to solve**: ~100-200
- **Optimal path length**: 8 steps
- **Final policy**: Diagonal path to goal

### Autonomous Car
- **Initial behavior**: Random lane changes, frequent collisions
- **After 50 episodes**: Basic lane keeping
- **After 150+ episodes**: Smooth navigation, strategic lane changes
- **Final distance**: 400-500m per episode

### CartPole
- **Random policy**: ~20-30 steps
- **Partially trained**: 100-150 steps
- **Solved (195+ avg)**: Usually by episode 150-250
- **Expert policy**: Consistent 200+ steps

---

## 🐛 Troubleshooting

**Issue**: Plots not showing
- **Solution**: Ensure `matplotlib` backend supports interactive mode
- Try: `export MPLBACKEND=TkAgg` before running

**Issue**: Training is slow
- **Solution**: Reduce `render_interval` or use CPU-only PyTorch
- Try: Disable visualization for pure training

**Issue**: CartPole not solving
- **Solution**: Training can be stochastic, try:
  - Increase episodes to 400-500
  - Adjust learning rate
  - Check epsilon decay isn't too fast

---

## 🎯 Next Steps

1. **Experiment**: Modify rewards, network architecture, hyperparameters
2. **Compare**: Try different algorithms (DQN vs Double DQN vs Dueling DQN)
3. **Extend**: Add new environments (LunarLander, MountainCar)
4. **Optimize**: Implement prioritized experience replay
5. **Scale**: Try multi-agent RL or continuous action spaces

---

## 📖 Further Reading

- [Sutton & Barto - Reinforcement Learning Book](http://incompleteideas.net/book/the-book.html)
- [Deep Q-Network Paper (DeepMind)](https://www.nature.com/articles/nature14236)
- [OpenAI Spinning Up in Deep RL](https://spinningup.openai.com/)
- [Gymnasium Documentation](https://gymnasium.farama.org/)

---

## 🤝 Contributing

Feel free to:
- Add new environments
- Implement different RL algorithms
- Improve visualizations
- Optimize performance

---

## 📝 License

MIT License - Feel free to use for learning and research!

---

**Happy Learning! 🚀**

*Remember: RL agents learn through trial and error - just like us!*
