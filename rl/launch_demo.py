#!/usr/bin/env python3
"""
Interactive launcher for RL demonstrations
"""

import sys

DEMOS = {
    '1': {
        'name': 'Grid World (Basic Q-Learning)',
        'file': 'grid_world_hello.py',
        'description': 'Simple 5x5 grid navigation with tabular Q-learning',
        'time': '~10 seconds',
        'visual': 'ASCII policy map'
    },
    '2': {
        'name': 'CartPole (Deep Q-Network with Neural Viz)',
        'file': 'cartpole_visual.py',
        'description': 'Balance pole on cart with DQN + neural network visualization',
        'time': '~5-10 minutes',
        'visual': 'Live physics simulation + neural network activations'
    },
    '3': {
        'name': 'Autonomous Car (Advanced DQN)',
        'file': 'autonomous_car_dqn.py',
        'description': 'Self-driving car navigating highway traffic',
        'time': '~10-15 minutes',
        'visual': 'Highway simulation + training metrics dashboard'
    }
}

def print_banner():
    print("\n" + "="*70)
    print(" " * 15 + "REINFORCEMENT LEARNING DEMOS")
    print("="*70)

def print_menu():
    print("\nAvailable Demonstrations:\n")
    for key, demo in DEMOS.items():
        print(f"[{key}] {demo['name']}")
        print(f"    {demo['description']}")
        print(f"    ⏱️  Estimated time: {demo['time']}")
        print(f"    🎨 Visual: {demo['visual']}")
        print()

def main():
    print_banner()
    print_menu()

    print("Which demo would you like to run?")
    print("[1-3] Select demo | [Q] Quit | [T] Run tests")
    print("="*70)

    choice = input("\nYour choice: ").strip().upper()

    if choice == 'Q':
        print("\nGoodbye!")
        sys.exit(0)
    elif choice == 'T':
        print("\nRunning component tests...\n")
        import subprocess
        subprocess.run([sys.executable, 'test_demos.py'])
        sys.exit(0)
    elif choice in DEMOS:
        demo = DEMOS[choice]
        print(f"\n🚀 Launching: {demo['name']}")
        print(f"📝 {demo['description']}")
        print(f"⏱️  This will take approximately {demo['time']}")
        print("\nPress Ctrl+C to stop the demo at any time.\n")
        print("="*70 + "\n")

        import subprocess
        try:
            subprocess.run([sys.executable, demo['file']])
        except KeyboardInterrupt:
            print("\n\nDemo stopped by user.")
    else:
        print(f"\nInvalid choice: {choice}")
        print("Please select 1, 2, 3, T, or Q")

if __name__ == "__main__":
    main()
