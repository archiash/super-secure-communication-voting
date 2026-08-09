from math import ceil
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2 as AerSampler
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_ibm_runtime.exceptions import IBMInputValueError, IBMError
from qiskit.transpiler import generate_preset_pass_manager

generate_bitcount = 32

USE_IBM_QUANTUM = True
IBM_TOKEN = "PUAAdh3bP7hCvVG6fQnGvF3pEv3Ti6PutxwsFKMG1CDI"

def random_binary(number_of_bit: int, use_ibm: bool = USE_IBM_QUANTUM):
    qc = QuantumCircuit(number_of_bit)

    for i in range(number_of_bit):
        qc.h(i)

    qc.measure_all()

    run_result = run_quantum_circuit(qc, use_ibm=use_ibm)

    return run_result[0]

def run_simulation(qc, times = 1):
    sampler = AerSampler()
    job = sampler.run([qc], shots=times)

    return [b[::-1] for b in job.result()[0].data.meas.get_bitstrings()]

def run_ibm_hardware(qc, times = 1, token = IBM_TOKEN):
    service = QiskitRuntimeService(
        channel="ibm_quantum_platform",
        token=token,
    )

    backend = service.least_busy(operational=True, simulator=False)

    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_qc = pm.run(qc)

    sampler = Sampler(mode=backend)
    job = sampler.run([isa_qc], shots=times)
    result = job.result()

    return [b[::-1] for b in result[0].data.meas.get_bitstrings()]

def run_quantum_circuit(qc, times = 1, use_ibm: bool = USE_IBM_QUANTUM):
    if use_ibm:
        return run_ibm_hardware(qc, times)
    else:
        return run_simulation(qc, times)

def simulate_bb84_protocal(key_size = 64, per_time_bit = 64, has_eavesdropping = False, use_ibm: bool = USE_IBM_QUANTUM):
    sending_key = random_binary(key_size, use_ibm=use_ibm)
    encryption_basis = random_binary(key_size, use_ibm=use_ibm)
    decryption_basis = random_binary(key_size, use_ibm=use_ibm)

    qc = sending_qubit(sending_key, encryption_basis)

    if has_eavesdropping:
        eavesdropping_basis = random_binary(key_size, use_ibm=use_ibm)
        eavesdropping_result = eavesdropping(qc, eavesdropping_basis, use_ibm=use_ibm)

        qc = eavesdropping_result["fake_qc"]

    qc = receive_qubit(qc, decryption_basis)

    qc.measure_all()

    run_result = run_quantum_circuit(qc, use_ibm=use_ibm)

    receive_key = run_result[0]

    result_report = {
        "server_key" : sending_key,
        "server_encryption_basis" : encryption_basis,
        "client_decryption_basis" : decryption_basis,
        "client_key" : receive_key
    }

    if has_eavesdropping:
        result_report |= {
            "eavesdropping_basis" : eavesdropping_basis,
            "eavesdropping_key" : eavesdropping_result["eavesdropping_key"]
        }

    return result_report

def eavesdropping(qc, basis, use_ibm: bool = USE_IBM_QUANTUM):
    eve_qc = receive_qubit(qc, basis)
    eve_qc.measure_all()

    run_result = run_quantum_circuit(eve_qc, use_ibm=use_ibm)

    receive_key = run_result[0]

    fake_qc = sending_qubit(receive_key, basis)

    return {
        "eavesdropping_copy" : fake_qc,
        "eavesdropping_key" : receive_key
    }

def sending_qubit(data, basis):
    qc = QuantumCircuit(len(data))

    for i in range(len(data)):
        if data[i] == '1':
            qc.x(i)

    for i in range(len(basis)):
        if basis[i] == '1':
            qc.h(i)

    return qc

def get_match_indexes(encrypt_basis, decrypt_basis):
    match_indexes = []

    for i in range(len(encrypt_basis)):
        if encrypt_basis[i] == decrypt_basis[i]:
            match_indexes.append(i)

    return match_indexes

def receive_qubit(qc, basis):
    for i in range(len(basis)):
        if basis[i] == '1':
            qc.h(i)

    return qc

def bitstring_from_index(bitstring, index):
    result_bitstring = ""

    for i in index:
        result_bitstring += bitstring[i]

    return result_bitstring

def sifting(key, basis1, basis2):
    match_basis_indexes = get_match_indexes(basis1, basis2)
    sifted_key = ""

    for i in range(len(key)): 
        sifted_key += key[i]

    return sifted_key

