import sys
import json
import random
import main as shor_main
from collections import Counter

def add_measurement_noise(counts, p_error):
    # simulate measurement error flipping classical bits with probability p_error
    noisy = Counter()
    for bitstring, count in counts.items():
        bit = bitstring[0]
        for _ in range(count):
            noisy_bit = '1' if bit == '0' and random.random() < p_error else bit
            noisy[noisy_bit] += 1
    return dict(noisy)


def run_single_noisy(index, input_state, arbitrary_error, qubit_error, p_error, shots=1):
    # build original Shor circuit and add classical noise to final logical measurement
    qc = shor_main.build_circuit(index, input_state, arbitrary_error, qubit_error)
    ideal_counts = shor_main.run_simulation(qc, shots)
    return add_measurement_noise(ideal_counts, p_error)


def run_multi_noisy(index, input_state, arbitrary_error, qubit_error, p_error, n_rounds=3, shots=1):
    # repeat full Shor circuit n times, each round gives noisy logical bit
    logical_bits = []
    for _ in range(n_rounds):
        noisy_counts = run_single_noisy(index, input_state, arbitrary_error, qubit_error, p_error, shots)
        # pick most likely bit from this round's noisy measurement
        bit = max(noisy_counts, key=noisy_counts.get)[0]
        logical_bits.append(bit)
    # majority vote: most frequent bit
    majority_bit = Counter(logical_bits).most_common(1)[0][0]
    return majority_bit


def compare_methods(num_trials, p_error, n_rounds):
    # compare error correction success rates
    single_success, multi_success = 0, 0
    
    for _ in range(num_trials):
        input_state = random.randint(0, 1)
        index = random.randint(0, 26)
        
        # noisy single round
        noisy_single = run_single_noisy(index, input_state, None, None, p_error)
        estimated_single = max(noisy_single, key=noisy_single.get)[0]
        if estimated_single == str(input_state):
            single_success += 1
        
        # noisy multi-round
        majority_bit = run_multi_noisy(index, input_state, None, None, p_error, n_rounds)
        if majority_bit == str(input_state):
            multi_success += 1
    
    # calculate success probabilities
    single_rate = single_success / num_trials
    multi_rate = multi_success / num_trials
    print(f"Out of {num_trials} trials with {p_error:.1f} measurement error probability and {n_rounds} rounds")
    print(f"Single round success: {single_rate:.1%}")
    print(f"Multi-round success: {multi_rate:.1%}")
    return {
        "num_trials": num_trials,
        "measurement_error_probability": p_error,
        "num_rounds": n_rounds,
        "single_round_success_rate": single_rate,
        "multi_round_success_rate": multi_rate,
    }

if __name__ == "__main__":
    num_trials = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    p_error = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    n_rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    results = compare_methods(num_trials, p_error, n_rounds)
    print(json.dumps(results))
