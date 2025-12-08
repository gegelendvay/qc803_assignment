from qiskit import QuantumCircuit, ClassicalRegister

# 9 data qubits + 6 ancilla qubits for Z-type syndrome + 2 ancilla qubits for X-type syndrome
qc = QuantumCircuit(17)
blocks = [(0,1,2), (3,4,5), (6,7,8)]
ancillas_z = [(9,10), (11,12), (13,14)]
ancillas_x = [15,16]

# classical registers for syndrome measurement outcomes
cr_z = []
for i in range(3):
    cr_z.append(ClassicalRegister(2, f'cr_z{i}'))
    qc.add_register(cr_z[i])
cr_x = ClassicalRegister(2, 'cr_x')
qc.add_register(cr_x)

# -- encoding --
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

# -------------------------------------
import random
for q in range(9):
    r = random.random()
    if r < 1/9:
        qc.x(q)
    elif r < 2/9:
        qc.z(q)
    else:
        qc.y(q)
qc.barrier()
# -------------------------------------

# -- Z-type syndrome measurement for X errors (bit flips) --
for i, block in enumerate(blocks):
    a1, a2 = ancillas_z[i]
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

# -- X-type syndrome measurement for Z errors (phase flips) --
# HXH = Z
for i in range(9):
    qc.h(i)
# S1 = X0 X1 X2 X3 X4 X5
for i in range(6):
    qc.cx(i, ancillas_x[0])
qc.measure(ancillas_x[0], cr_x[0])
# S2 = X3 X4 X5 X6 X7 X8
for i in range(3, 9):
    qc.cx(i, ancillas_x[1])
qc.measure(ancillas_x[1], cr_x[1])
# reverse HXH
for i in range(9):
    qc.h(i)

qc.barrier()
'''for i in range(9,17):
    qc.reset(i)'''

# -- bit-flip correction (X errors) using Z-type syndromes --
for i, block in enumerate(blocks):
    q0, q1, q2 = block
    with qc.if_test((cr_z[i], 0b01)):
        qc.x(q0)
    with qc.if_test((cr_z[i], 0b10)):
        qc.x(q1)
    with qc.if_test((cr_z[i], 0b11)):
        qc.x(q2)

qc.barrier()

# -- phase-flip correction (Z errors) using X-type syndromes --
with qc.if_test((cr_x, 0b01)):
    qc.z(0)
with qc.if_test((cr_x, 0b10)):
    qc.z(3)
with qc.if_test((cr_x, 0b11)):
    qc.z(6)

qc.barrier()

# -- decoding --
for i in [0,3,6]:
    qc.cx(i, i+1)
    qc.cx(i, i+2)
    qc.ccx(i+1, i+2, i)
    qc.h(i)
qc.cx(0,3)
qc.cx(0,6)
qc.ccx(3,6,0)
result = ClassicalRegister(1, 'logical_result')
qc.add_register(result)
qc.measure(0, result[0])


'''
# simulation (then to try with different errors above)
from qiskit_aer import AerSimulator
backend = AerSimulator()
job = backend.run(qc, shots=1024).result()
counts = job.get_counts()
print(counts)
# {'1 00 00 10 00': 1024} something wrong with this result

# Draw and save the circuit
fig = qc.draw('mpl', fold=False, cregbundle=False)
fig.savefig("circuit.png")
'''
