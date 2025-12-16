# https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction/correcting-quantum-errors/shor-code
import sys
import random
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

def inject_error(qc, index=-1):
    # different error on each repetition in a loop (27 repetitions to cover all single-qubit errors)
    if index < 9:
        qc.x(index)
    elif index < 18:
        qc.z(index-9)
    elif index < 27:
        qc.y(index-18)
    # pauli error with p=1/3 on a random qubit
    else:
        r = random.random()
        q = random.randint(0,8)
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

def build_circuit(index, input_state):
    qc, cr_z, cr_x, result = create_circuit(input_state)

    encode_qubit(qc)
    inject_error(qc, index)
    measure_z_syndrome(qc, cr_z)
    measure_x_syndrome(qc, cr_x)
    # reset_ancillas(qc)
    correct_bit_flips(qc, cr_z)
    correct_phase_flips(qc, cr_x)
    decode_qubit(qc)
    measure(qc, result)

    return qc

def run_simulation(qc, shots=1):
    backend = AerSimulator()
    job = backend.run(qc, shots=shots).result()
    return job.get_counts()

# run simulation for n times given as command line argument
n = int(sys.argv[1])
for s in range(n):
    input_state = random.choice([0,1])
    qc = build_circuit(s, input_state)

    # print only if logical qubit measurement is different from input state
    counts = run_simulation(qc)
    if next(iter(counts))[0] != str(input_state):
        print(f"{s}: {input_state} -> {counts.keys()}")

'''
# Draw and save the circuit
fig = qc.draw('mpl', fold=False, cregbundle=False)
fig.savefig("circuit.png")
'''
