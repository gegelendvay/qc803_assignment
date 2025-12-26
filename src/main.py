import argparse
import random

import matplotlib.pyplot as plt
from qiskit import ClassicalRegister, QuantumCircuit
from qiskit_aer import AerSimulator
from collections import Counter

backend = AerSimulator()

DATA_QUBITS = list(range(9))
BLOCKS = [(0,1,2), (3,4,5), (6,7,8)]
ANCILLAS_Z = [(9,10), (11,12), (13,14)]
ANCILLAS_X = [15,16]

def create_circuit(input_state) -> QuantumCircuit:
    """Create a 17 qubit Shor's code cicuit with 9 data qubits, 6 ancilla qubits for Z-type syndrome, and 2 ancilla qubits for X-type syndrome.

    Args:
        input_state (int): Logical input state

    Returns:
        QuantumCircuit: The initialized quantum circuit.
    """

    qc = QuantumCircuit(17)

    if input_state == 1:
        qc.x(0)  # prepare logical |1> state

    # classical registers for syndrome measurement outcomes
    cr_z = []
    for i in range(3):
        register = (ClassicalRegister(2, f"cr_z{i}"))
        qc.add_register(register)
        cr_z.append(register)

    cr_x = ClassicalRegister(2, "cr_x")
    qc.add_register(cr_x)

    # classical register for final logical qubit measurement
    result = ClassicalRegister(1, "logical_result")
    qc.add_register(result)
    return qc, cr_z, cr_x, result

def encode_qubit(qc) -> None:
    """Encode logical qubit into Shor code."""
    # spreads logical qubit to the first qubit of each block
    qc.cx(0,3)
    qc.cx(0,6)

    for i in [0,3,6]:
        # apply Hadamard to transform phase-flip to bit-flip
        qc.h(i)
        # apply bit-flip code within each block
        qc.cx(i, i+1)
        qc.cx(i, i+2)

    qc.barrier()

def inject_error_sequentially(qc, index) -> None:
    """Inject error sequentially."""

    if index < 9:
        qc.x(index)
    elif index < 18:
        qc.z(index-9)
    elif index < 27:
        qc.y(index-18)
    else:
        inject_error_sequentially(qc, index-27)

    qc.barrier()

def inject_arbitrary_error(qc, error_type, q) -> None:
    """Inject an arbitrary error."""

    q = q if q is not None else random.randint(0,8)
    if error_type == "x":
        qc.x(q)
    elif error_type == "z":
        qc.z(q)
    elif error_type == "y":
        qc.y(q)
    else:  # random error with equal probabilities
        r = random.random()
        if r < 1/3:
            qc.x(q)
        elif r < 2/3:
            qc.z(q)
        else:
            qc.y(q)

    qc.barrier()

def measure_z_syndrome(qc, cr_z) -> None:
    """Measure Z-type syndrome for X errors (bit flips)."""

    for i, block in enumerate(BLOCKS):
        a1, a2 = ANCILLAS_Z[i]
        cbits_z = cr_z[i]

        # S1 = Z_a Z_b
        qc.cx(block[0], a1)
        qc.cx(block[1], a1)
        qc.measure(a1, cbits_z[0])
        qc.reset(a1)

        # S2 = Z_b Z_c
        qc.cx(block[1], a2)
        qc.cx(block[2], a2)
        qc.measure(a2, cbits_z[1])
        qc.reset(a2)

    qc.barrier()

def measure_x_syndrome(qc, cr_x) -> None:
    """Measure X-type syndrome for Z errors (phase flips, HXH = Z)."""

    for i in DATA_QUBITS:
        qc.h(i)

    # S1 = X0 X1 X2 X3 X4 X5
    for i in range(6):
        qc.cx(i, ANCILLAS_X[0])
    qc.measure(ANCILLAS_X[0], cr_x[0])
    qc.reset(ANCILLAS_X[0])

    # S2 = X3 X4 X5 X6 X7 X8
    for i in range(3, 9):
        qc.cx(i, ANCILLAS_X[1])
    qc.measure(ANCILLAS_X[1], cr_x[1])
    qc.reset(ANCILLAS_X[1])

    # reverse HXH
    for i in DATA_QUBITS:
        qc.h(i)

    qc.barrier()

def correct_bit_flips(qc, cr_z) -> None:
    """Correct bit flips (X errors) using Z-type syndromes."""

    for i, block in enumerate(BLOCKS):
        q0, q1, q2 = block
        with qc.if_test((cr_z[i], 0b01)):
            qc.x(q0)
        with qc.if_test((cr_z[i], 0b11)):
            qc.x(q2)
        with qc.if_test((cr_z[i], 0b10)):
            qc.x(q1)

    qc.barrier()

def correct_phase_flips(qc, cr_x) -> None:
    """Correct phase flips (Z errors) using X-type syndromes."""

    with qc.if_test((cr_x, 0b01)):
        qc.z(0)
    with qc.if_test((cr_x, 0b11)):
        qc.z(3)
    with qc.if_test((cr_x, 0b10)):
        qc.z(6)

    qc.barrier()

def decode_qubit(qc) -> None:
    """Decode the logical qubit."""

    for i in [0,3,6]:
        qc.cx(i, i+1)
        qc.cx(i, i+2)
        qc.ccx(i+1, i+2, i)
        qc.h(i)
    qc.cx(0,3)
    qc.cx(0,6)
    # double check logical qubit decoding
    qc.ccx(3,6,0)

def measure(qc, result) -> None:
    """Measure the logical qubit."""

    qc.measure(0, result[0])

def build_circuit(index, input_state, arbitrary_error, qubit_error) -> QuantumCircuit:
    """Build the quantum circuit for the Shor's code."""

    qc, cr_z, cr_x, result = create_circuit(input_state)

    encode_qubit(qc)
    if arbitrary_error is None and qubit_error is None:
        inject_error_sequentially(qc, index)
    else:
        inject_arbitrary_error(qc, arbitrary_error, qubit_error)
    measure_z_syndrome(qc, cr_z)
    measure_x_syndrome(qc, cr_x)
    correct_bit_flips(qc, cr_z)
    correct_phase_flips(qc, cr_x)
    decode_qubit(qc)
    measure(qc, result)

    return qc

def run_simulation(qc, shots=1) -> dict:
    """Run the quantum circuit simulation."""

    backend = AerSimulator()
    # single shot is enough as there is no randomness in the circuit
    job = backend.run(qc, shots=shots).result()
    return job.get_counts()

def positive_int(value) -> int:
    """Check that the num-simulations value is a positive integer."""

    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "num-simulations must be a positive integer (> 0)",
        )
    return ivalue

def int_range(min_val, max_val) -> callable:
    """Check that the qubit-error value is in the range of the data qubits."""
    def _range_checker(value) -> int:
        """Check that the qubit-error value is in the range of the data qubits."""
        ivalue = int(value)
        if ivalue < min_val or ivalue > max_val:
            msg = f"qubit-error must be in range [{min_val}, {max_val}]"
            raise argparse.ArgumentTypeError(msg)
        return ivalue
    return _range_checker

def plot_histogram(counts) -> None:
    """Plot the histogram of measurement results."""

    results = {"0": 0, "1": 0}
    for key, value in counts.items():
        results[key[0]] += value

    plt.bar(results.keys(), results.values())
    plt.xlabel("Measurement Results")
    plt.ylabel("Counts")
    plt.title("Measurement Results")
    plt.savefig("results_histogram.png")

def parse_arguments() -> argparse.ArgumentParser:
    """Parser for command line arguments."""
    parser = argparse.ArgumentParser(
        description="Shor's code QEC simulation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--num-simulations",
        type=positive_int,
        default=1,
        help="Number of simulations (positive integer)",
    )

    parser.add_argument(
        "--arbitrary-error",
        choices=["x", "y", "z"],
        help="Arbitrary error type",
    )

    parser.add_argument(
        "--qubit-error",
        type=int_range(0, 8),
        help="Qubit on which apply the error (integer from 0 to 8)",
    )

    parser.add_argument(
        "--input-state",
        type=int,
        choices=[0, 1],
        help="Initial logical state",
    )

    parser.add_argument(
        "--draw-circuit",
        default=False,
        action="store_true",
        help="Draw all circuits simulated and save as PNG file",
    )

    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()

    # run simulation for n times given as command line argument
    correctness = True
    total_counts = Counter()
    n = args.num_simulations

    # retrieve input state or choose randomly for each simulation
    input_state = (args.input_state if args.input_state is not None else random.randint(0, 1))
    
    for s in range(args.num_simulations):
        # build circuit with (un)specified errors
        qc = build_circuit(s, input_state, args.arbitrary_error, args.qubit_error)

        # print measurement only if final measurement is different from input state
        counts = run_simulation(qc, shots=1)
        total_counts.update(counts)
        if next(iter(counts))[0] != str(input_state):
            correctness = False
            print(f"{s}: {input_state} -> {counts.keys()}")

        # draw circuit if requested
        if args.draw_circuit:
            fig = qc.draw("mpl", fold=False, cregbundle=False)
            fig.savefig(f"circuit_{s}.png")

    # print overall correctness
    if correctness:
        print("All simulations correct!")
    plot_histogram(total_counts)