import argparse
import pytest
from qiskit import QuantumCircuit

import src.main as sc

# Functions, such as plot_histogram(), parse_arguments(), as well as the script entry block (__main__) are skipped from coverage because:
# 1. They don't contain core computational logic
# 2. Testing them would require GUI interactions, command-line argument manipulation, or full script execution, all of which are outside the scope of unit tests
# 3. Skipping them allows the coverage to focus on the actual logic 

def create_test_circuit(input_state=0):
    qc, cr_z, cr_x, result = sc.create_circuit(input_state)
    return qc, cr_z, cr_x, result

# create_circuit()
def test_create_circuit():
    qc, _cr_z, _cr_x, _result = create_test_circuit()
    assert isinstance(qc, QuantumCircuit)

# encode_qubit()
def test_encode_qubit():
    qc, _cr_z, _cr_x, _result = create_test_circuit()
    sc.encode_qubit(qc)

    assert qc.count_ops().get("cx", 0) == 8
    assert qc.count_ops().get("h", 0) == 3

# inject_error_sequentially()
def test_inject_error_sequentially():
    qc, _cr_z, _cr_x, _result = create_test_circuit()
    sc.inject_error_sequentially(qc, 0)
    assert qc.count_ops().get("x", 0) == 1
    sc.inject_error_sequentially(qc, 10)
    assert qc.count_ops().get("z", 0) == 1

# inject_arbitrary_error()
def test_inject_arbitrary_error():
    qc, _cr_z, _cr_x, _result = create_test_circuit()
    sc.inject_arbitrary_error(qc, "x", 0)
    assert qc.count_ops().get("x", 0) == 1
    sc.inject_arbitrary_error(qc, "z", 1)
    assert qc.count_ops().get("x", 0) == 1
    sc.inject_arbitrary_error(qc, "y", 2)
    assert qc.count_ops().get("x", 0) == 1

# measure_z_syndrome()
def test_measure_z_syndrome():
    qc, cr_z, _cr_x, _result = create_test_circuit()
    sc.measure_z_syndrome(qc, cr_z)
    assert qc.count_ops().get("cx", 0) == 12
    assert qc.count_ops().get("measure", 0) == 6

# measure_x_syndrome()
def test_measure_x_syndrome():
    qc, _cr_z, cr_x, _result = create_test_circuit()
    sc.measure_x_syndrome(qc, cr_x)
    assert qc.count_ops().get("h", 0) == 18
    assert qc.count_ops().get("cx", 0) == 12
    assert qc.count_ops().get("measure", 0) == 2

# correct_bit_flips()
def test_correct_bit_flips():
    qc, cr_z, _cr_x, _result = create_test_circuit()
    sc.correct_bit_flips(qc, cr_z)
    assert qc.count_ops().get("x", 0) == 0

# correct_phase_flips()
def test_correct_phase_flips():
    qc, _cr_z, cr_x, _result = create_test_circuit()
    sc.correct_phase_flips(qc, cr_x)
    assert qc.count_ops().get("z", 0) == 0

# decode_qubit()
def test_decode_qubit():
    qc, _cr_z, _cr_x, _result = create_test_circuit()
    sc.decode_qubit(qc)
    assert qc.count_ops().get("cx", 0) == 8
    assert qc.count_ops().get("ccx", 0) == 4
    assert qc.count_ops().get("h", 0) == 3

# measure()
def test_measure():
    qc, _cr_z, _cr_x, result = create_test_circuit()
    sc.measure(qc, result)
    assert qc.count_ops().get("measure", 0) == 1

# build_circuit()
def test_build_circuit():
    qc = sc.build_circuit(0, 0, None, None)
    counts = sc.run_simulation(qc)
    assert isinstance(counts, dict)
    assert len(counts) >= 1

def test_build_circuit_2():
    qc = sc.build_circuit(0, 0, 2, 1) #What errors should we use here?
    counts = sc.run_simulation(qc)
    assert isinstance(counts, dict)
    assert len(counts) >= 1

# positive_int()
def test_positive_int_valid():
    assert sc.positive_int("1") == 1
    assert sc.positive_int("10") == 10

def test_positive_int_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        sc.positive_int("0")
    with pytest.raises(argparse.ArgumentTypeError):
        sc.positive_int("-3")

# int_range()
def test_int_range_valid():
    assert sc.int_range(0, 8)("0") == 0
    assert sc.int_range(0, 8)("8") == 8

def test_int_range_invalid():
    with pytest.raises(argparse.ArgumentTypeError):
        sc.int_range(0, 8)("-1")
    with pytest.raises(argparse.ArgumentTypeError):
        sc.int_range(0, 8)("9")

# parse_arguments()
# Should we test this function?
