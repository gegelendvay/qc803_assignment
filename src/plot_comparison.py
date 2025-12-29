import json
import subprocess
import numpy as np
import matplotlib.pyplot as plt

num_trials = 500

def run_experiment(num_trials, p_error, n_rounds):
    # execute main_noisy.py with given parameters
    cmd = ['python', 'main_noisy.py', str(num_trials), str(p_error), str(n_rounds)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running: {' '.join(cmd)}")
        print(result.stderr)
        return None
    
    # parse JSON from last line of output
    lines = result.stdout.strip().split('\n')
    if not lines:
        return None
    
    # returns dict with success rates or None on error.
    try:
        results = json.loads(lines[-1])
        return results
    except json.JSONDecodeError:
        print("Failed to parse JSON output")
        print("Last 200 chars:", result.stdout[-200:])
        return None

def sweep_measurement_error():
    # test success rates across measurement error probabilities (0% to 50%)
    n_rounds = 3
    p_errors = np.linspace(0, 0.5, 11)
    
    single_rates = []
    multi_rates = []
    
    for p_error in p_errors:
        print(f"Testing p_error={p_error:.2f}")
        results = run_experiment(num_trials, p_error, n_rounds)
        if results:
            single_rates.append(results["single_round_success_rate"])
            multi_rates.append(results["multi_round_success_rate"])
        else:
            print(f"  -> SKIPPED")
    
    # trim arrays to matching length (in case of failures)
    min_len = min(len(single_rates), len(multi_rates))
    return (p_errors[:min_len], 
            np.array(single_rates[:min_len]), 
            np.array(multi_rates[:min_len]))

def sweep_num_rounds():
    # test success rates across number of syndrome rounds (1 to 7)
    p_error = 0.2
    n_rounds_list = [1, 3, 5, 7]
    
    single_rates = []
    multi_rates = []
    
    for n_rounds in n_rounds_list:
        print(f"Testing n_rounds={n_rounds}")
        results = run_experiment(num_trials, p_error, n_rounds)
        if results:
            single_rates.append(results["single_round_success_rate"])
            multi_rates.append(results["multi_round_success_rate"])
    
    return n_rounds_list, np.array(single_rates), np.array(multi_rates)

if __name__ == "__main__":
    # create side-by-side plots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # success vs measurement error probability
    p_errors, single_err, multi_err = sweep_measurement_error()
    ax1.plot(p_errors*100, single_err, 'ro-', label='Single round', 
             linewidth=3, markersize=8)
    ax1.plot(p_errors*100, multi_err, 'bs-', label='3-round majority', 
             linewidth=3, markersize=8) 
    ax1.set_xlabel('Measurement error probability (%)', fontsize=12)
    ax1.set_ylabel('Logical success rate', fontsize=12)
    ax1.set_title('Error Correction vs Measurement Noise', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(fontsize=11)
    ax1.set_ylim(0, 1.05)
    
    # success vs number of rounds
    n_rounds, single_rnds, multi_rnds = sweep_num_rounds()
    ax2.plot(n_rounds, single_rnds, 'ro-', label='Single round (baseline)', 
             linewidth=3, markersize=8)
    ax2.plot(n_rounds, multi_rnds, 'bs-', label='Multi-round majority', 
             linewidth=3, markersize=8)
    ax2.set_xlabel('Number of syndrome measurement rounds', fontsize=12)
    ax2.set_ylabel('Logical success rate', fontsize=12)
    ax2.set_title('Success vs Rounds (20% Measurement Error)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=11)
    ax2.set_ylim(0, 1.05)
    
    plt.tight_layout()
    plt.savefig('shor_syndrome_comparison.png', dpi=300, bbox_inches='tight')
    print("\nPlot saved: 'shor_syndrome_comparison.png'")
