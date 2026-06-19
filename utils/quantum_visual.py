import matplotlib.pyplot as plt
import numpy as np
import os


def quantum_plot(save_path="static/uploads/quantum_state.png"):

    # Simulated quantum probability amplitudes
    states = np.random.rand(6)

    states = states / np.sum(states)   # Normalize probabilities

    plt.figure(figsize=(6,4))
    plt.bar(range(len(states)), states)
    plt.title("Quantum Processing State Simulation")
    plt.xlabel("Quantum State")
    plt.ylabel("Probability Amplitude")

    plt.tight_layout()

    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path)
    plt.close()

    return save_path
