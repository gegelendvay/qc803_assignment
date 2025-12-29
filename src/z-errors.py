import random
from collections import Counter
from qiskit import QuantumCircuit
from main import create_circuit, encode_qubit, measure_z_syndrome, measure_x_syndrome, decode_qubit, measure, run_simulation, plot_histogram, inject_arbitrary_error


def build_circuit(index, input_state) -> QuantumCircuit:
    """Build the quantum circuit for the Shor's code."""
    qc, cr_z, cr_x, result = create_circuit(input_state)

    encode_qubit(qc)
    inject_arbitrary_error(qc, "z", index)
    measure_z_syndrome(qc, cr_z)
    measure_x_syndrome(qc, cr_x)
    decode_qubit(qc)
    measure(qc, result)

    return qc


if __name__ == "__main__":
    total_counts = Counter()

    relevant = False
    input_state = random.randint(0, 1)

    for s in range(9):
        qc = build_circuit(s, input_state)
        counts = run_simulation(qc, shots=1)
        total_counts.update(counts)

        registers_printout = str(list(counts.keys()))
        print(f"{s}: {input_state} -> {registers_printout}")
        if registers_printout[7:-2] != "00 00 00":
            relevant = True

    if not relevant:
        print("Only X-type errors detected as expected")
    plot_histogram(total_counts)
