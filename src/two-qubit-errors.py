import random
from collections import Counter
from qiskit import QuantumCircuit
from main import create_circuit, encode_qubit, measure_z_syndrome, measure_x_syndrome, correct_bit_flips, correct_phase_flips, decode_qubit, measure, plot_histogram, run_simulation


def inject_error_sequentially(qc, index) -> None:
    """Inject first error sequentially."""
    index = index % 27
    if index < 9:
        qc.x(index)
    elif index < 18:
        qc.z(index - 9)
    else:
        qc.y(index - 18)


def inject_second_error_sequentially(qc, index) -> None:
    """Inject a second error sequentially."""
    index = (index // 27) % 27
    if index < 9:
        qc.x(index)
    elif index < 18:
        qc.z(index - 9)
    else:
        qc.y(index - 18)


def build_circuit(index, input_state) -> QuantumCircuit:
    """Build the quantum circuit for the Shor's code."""
    qc, cr_z, cr_x, result = create_circuit(input_state)

    encode_qubit(qc)
    inject_error_sequentially(qc, index)
    inject_second_error_sequentially(qc, index)
    measure_z_syndrome(qc, cr_z)
    measure_x_syndrome(qc, cr_x)
    correct_bit_flips(qc, cr_z)
    correct_phase_flips(qc, cr_x)
    decode_qubit(qc)
    measure(qc, result)

    return qc


def decode_error_index(idx):
    """Decode both errors (for printing) from combined index."""
    idx1 = idx % 27
    idx2 = (idx // 27) % 27

    def decode_one(i):
        if i < 9:
            return 'X', i
        elif i < 18:
            return 'Z', i - 9
        else:
            return 'Y', i - 18

    return decode_one(idx1), decode_one(idx2)


if __name__ == "__main__":
    correctness = True
    total_counts = Counter()

    input_state = random.randint(0, 1)

    for s in range(27 * 27):
        qc = build_circuit(s, input_state)
        counts = run_simulation(qc, shots=1)
        total_counts.update(counts)

        meas = next(iter(counts))[0]
        if meas != str(input_state):
            correctness = False
            (p1, q1), (p2, q2) = decode_error_index(s)
            print(f"{p1}{q1} {p2}{q2}: {input_state} -> {list(counts.keys())}")

    if correctness:
        print("All simulations correct!")

    plot_histogram(total_counts)
