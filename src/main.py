# https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction/correcting-quantum-errors/shor-code
import sys
import random
import argparse
from qiskit_aer import AerSimulator
from qiskit import QuantumCircuit, ClassicalRegister

backend = AerSimulator()

DATA_QUBITS = list(range(9))
BLOCKS = [(0,1,2), (3,4,5), (6,7,8)]
ANCILLAS_Z = [(9,10), (11,12), (13,14)]
ANCILLAS_X = [15,16]

# 9 data qubits + 6 ancilla qubits for Z-type syndrome + 2 ancilla qubits for X-type syndrome
def create_circuit(input_state):
    qc = QuantumCircuit(17)

    if input_state == 1:
        qc.x(0)  # prepare logical |1> state

    # classical registers for syndrome measurement outcomes
    cr_z = []
    for i in range(3):
        register = (ClassicalRegister(2, f'cr_z{i}'))
        qc.add_register(register)
        cr_z.append(register)

    cr_x = ClassicalRegister(2, 'cr_x')
    qc.add_register(cr_x)

    # classical register for final logical qubit measurement
    result = ClassicalRegister(1, 'logical_result')
    qc.add_register(result)
    return qc, cr_z, cr_x, result

def encode_qubit(qc):
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

def inject_error_sequentially(qc, index):
    if index < 9:
        qc.x(index)
    elif index < 18:
        qc.z(index-9)
    elif index < 27:
        qc.y(index-18)
    else:
        inject_error_sequentially(qc, index-27)

    qc.barrier()

def inject_arbitrary_error(qc, error_type, q):
    q = q if q is not None else random.randint(0,8)
    if error_type == 'x':
        qc.x(q)
    elif error_type == 'z':
        qc.z(q)
    elif error_type == 'y':
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

def measure_z_syndrome(qc, cr_z):
    # -- Z-type syndrome measurement for X errors (bit flips) --
    for i, block in enumerate(BLOCKS):
        a1, a2 = ANCILLAS_Z[i]
        cbits_z = cr_z[i]

        # S1 = Z_a Z_b
        qc.cx(block[0], a1)
        qc.cx(block[1], a1)
        qc.measure(a1, cbits_z[0])

        # S2 = Z_b Z_c
        qc.cx(block[1], a2)
        qc.cx(block[2], a2)
        qc.measure(a2, cbits_z[1])

    qc.barrier()

def measure_x_syndrome(qc, cr_x):
    # -- X-type syndrome measurement for Z errors (phase flips, HXH = Z) --
    for i in DATA_QUBITS:
        qc.h(i)

    # S1 = X0 X1 X2 X3 X4 X5
    for i in range(6):
        qc.cx(i, ANCILLAS_X[0])
    qc.measure(ANCILLAS_X[0], cr_x[0])

    # S2 = X3 X4 X5 X6 X7 X8
    for i in range(3, 9):
        qc.cx(i, ANCILLAS_X[1])
    qc.measure(ANCILLAS_X[1], cr_x[1])

    # reverse HXH
    for i in DATA_QUBITS:
        qc.h(i)

    qc.barrier()

def reset_ancillas(qc):
    # after measurement, reset ancilla qubits for possible reuse
    for i in range(9,17):
        qc.reset(i)

def correct_bit_flips(qc, cr_z):
    # -- bit-flip correction (X errors) using Z-type syndromes --
    for i, block in enumerate(BLOCKS):
        q0, q1, q2 = block
        with qc.if_test((cr_z[i], 0b01)):
            qc.x(q0)
        with qc.if_test((cr_z[i], 0b11)):
            qc.x(q2)
        with qc.if_test((cr_z[i], 0b10)):
            qc.x(q1)

    qc.barrier()

def correct_phase_flips(qc, cr_x):
    # -- phase-flip correction (Z errors) using X-type syndromes --
    with qc.if_test((cr_x, 0b01)):
        qc.z(0)
    with qc.if_test((cr_x, 0b11)):
        qc.z(3)
    with qc.if_test((cr_x, 0b10)):
        qc.z(6)

    qc.barrier()

def decode_qubit(qc):
    # -- decoding --
    for i in [0,3,6]:
        qc.cx(i, i+1)
        qc.cx(i, i+2)
        qc.ccx(i+1, i+2, i)
        qc.h(i)
    # double check logical qubit decoding
    qc.cx(0,3)
    qc.cx(0,6)
    qc.ccx(3,6,0)

def measure(qc, result):
    # measure the logical qubit
    qc.measure(0, result[0])

def build_circuit(index, input_state, arbitrary_error, qubit_error):
    qc, cr_z, cr_x, result = create_circuit(input_state)

    encode_qubit(qc)
    if arbitrary_error is None and qubit_error is None:
        inject_error_sequentially(qc, index)
    else:
        inject_arbitrary_error(qc, arbitrary_error, qubit_error)
    measure_z_syndrome(qc, cr_z)
    measure_x_syndrome(qc, cr_x)
    # reset_ancillas(qc)
    correct_bit_flips(qc, cr_z)
    correct_phase_flips(qc, cr_x)
    decode_qubit(qc)
    measure(qc, result)

    return qc

def run_simulation(qc):
    backend = AerSimulator()
    # single shot is enough as there is no randomness in the circuit
    job = backend.run(qc, shots=1).result()
    return job.get_counts()

# check that num-simulations is a positive integer
def positive_int(value):
    ivalue = int(value)
    if ivalue <= 0:
        raise argparse.ArgumentTypeError(
            "num-simulations must be a positive integer (> 0)"
        )
    return ivalue

# check that qubit-error is in the range of the data qubits
def int_range(min_val, max_val):
    def _range_checker(value):
        ivalue = int(value)
        if ivalue < min_val or ivalue > max_val:
            raise argparse.ArgumentTypeError(
                f"qubit-error must be in range [{min_val}, {max_val}]"
            )
        return ivalue
    return _range_checker

# parser for command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Shor's code QEC simulation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "--num-simulations",
        type=positive_int,
        default=1,
        help="Number of simulations (positive integer)"
    )

    parser.add_argument(
        "--arbitrary-error",
        choices=["x", "y", "z"],
        help="Arbitrary error type"
    )

    parser.add_argument(
        "--qubit-error",
        type=int_range(0, 8),
        help="Qubit on which apply the error (integer from 0 to 8)"
    )

    parser.add_argument(
        "--input-state",
        type=int,
        choices=[0, 1],
        help="Initial logical state"
    )

    parser.add_argument(
        "--draw-circuit",
        default=False,
        action="store_true",
        help="Draw all circuits simulated and save as PNG file"
    )

    return parser.parse_args()

# parse command line arguments
args = parse_arguments()

# run simulation for n times given as command line argument
correctness = True
n = args.num_simulations

for s in range(args.num_simulations):
    # retrieve input state or choose randomly for each simulation
    if args.input_state is not None:
        input_state = args.input_state
    else:
        input_state = random.randint(0, 1)

    # build circuit with (un)specified errors
    qc = build_circuit(s, input_state, args.arbitrary_error, args.qubit_error)

    # print measurement only if final measurement is different from input state
    counts = run_simulation(qc)
    if next(iter(counts))[0] != str(input_state):
        correctness = False
        print(f"{s}: {input_state} -> {counts.keys()}")

    # draw circuit if requested
    if args.draw_circuit:
        fig = qc.draw('mpl', fold=False, cregbundle=False)
        fig.savefig(f"circuit_{s}.png")

# print overall correctness
if correctness:
    print(f"All simulations correct!")
