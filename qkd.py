from math import ceil
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.primitives import SamplerV2 as AerSampler
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_ibm_runtime.exceptions import IBMInputValueError, IBMError
from qiskit.transpiler import generate_preset_pass_manager

generate_bitcount = 32
key_size = 64

# Execution Mode Toggle: Set to True for real IBM Quantum hardware, False for local Aer simulator
USE_IBM_QUANTUM = True

# IBM Quantum Authentication Configuration:
# - IBM_TOKEN: Provide your IBM Quantum Platform API token (from https://quantum.ibm.com)
# - IBM_INSTANCE: Optional IBM Cloud CRN or instance name (leave None for default open instance)
IBM_TOKEN = "PUAAdh3bP7hCvVG6fQnGvF3pEv3Ti6PutxwsFKMG1CDI"
IBM_INSTANCE = None

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
    # Qiskit get_bitstrings() returns little-endian bitstrings ("q_{N-1}...q_0").
    # Reversing each string with [::-1] aligns index i of the string with qubit i.
    return [b[::-1] for b in job.result()[0].data.meas.get_bitstrings()]

_ibm_fallback_active = False

def run_ibm_hardware(qc, times = 1, token = IBM_TOKEN, instance = IBM_INSTANCE):
    global _ibm_fallback_active

    if _ibm_fallback_active:
        return run_simulation(qc, times)

    try:
        if token:
            service = QiskitRuntimeService(
                channel="ibm_quantum_platform",
                token=token,
                instance=instance
            )
        else:
            service = QiskitRuntimeService(instance=instance)

        backend = service.least_busy(operational=True, simulator=False)
        print(f"Connected to IBM Quantum backend: {backend.name}")

        pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
        isa_qc = pm.run(qc)

        sampler = Sampler(mode=backend)
        job = sampler.run([isa_qc], shots=times)
        result = job.result()

        return [b[::-1] for b in result[0].data.meas.get_bitstrings()]

    except Exception as e:
        _ibm_fallback_active = True
        print("\n[WARNING] IBM Quantum Hardware Connection Failed!")
        print(f"Details: {e}")
        print("\n--- Troubleshooting IBM Quantum Connection ---")
        print("1. Get a valid IBM Quantum API token from https://quantum.ibm.com")
        print("2. Set IBM_TOKEN = 'YOUR_API_TOKEN' at the top of qkd.py")
        print("3. Ensure your IBM Quantum account has an active quantum instance/plan.")
        print("\n[FALLBACK] Running on local Aer simulator for all remaining calls...\n")
        return run_simulation(qc, times)

def run_quantum_circuit(qc, times = 1, use_ibm: bool = USE_IBM_QUANTUM):
    if use_ibm:
        return run_ibm_hardware(qc, times)
    else:
        return run_simulation(qc, times)

def simulate_quantum_channel(has_evedroping = False, use_ibm: bool = USE_IBM_QUANTUM):
    sending_key = random_binary(key_size, use_ibm=use_ibm)
    encryption_basis = random_binary(key_size, use_ibm=use_ibm)
    decryption_basis = random_binary(key_size, use_ibm=use_ibm)

    qc = sending_qubit(sending_key, encryption_basis)

    if has_evedroping:
        evedroping_basis = random_binary(key_size, use_ibm=use_ibm)
        evedroping_result = evedroping(qc, evedroping_basis, use_ibm=use_ibm)

        qc = evedroping_result["fake_qc"]

    qc = receive_qubit(qc, decryption_basis)

    qc.measure_all()

    run_result = run_quantum_circuit(qc, use_ibm=use_ibm)

    receive_key = run_result[0]

    result_report = {
        "sent_key" : sending_key,
        "encryption_basis" : encryption_basis,
        "decryption_basis" : decryption_basis,
        "received_key" : receive_key
    }

    if has_evedroping:
        result_report |= {
            "evedroping_basis" : evedroping_basis,
            "evedroping_key" : evedroping_result["evedrop_key"]
        }

    return result_report

def evedroping(qc, basis, use_ibm: bool = USE_IBM_QUANTUM):
    eve_qc = receive_qubit(qc, basis)
    eve_qc.measure_all()

    run_result = run_quantum_circuit(eve_qc, use_ibm=use_ibm)

    receive_key = run_result[0]

    fake_qc = sending_qubit(receive_key, basis)

    return {
        "fake_qc" : fake_qc,
        "evedrop_key" : receive_key
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

def compare_basis(encrypt_basis, decrypt_basis):
    match_index = []

    for i in range(len(encrypt_basis)):
        if encrypt_basis[i] == decrypt_basis[i]:
            match_index.append(i)

    return match_index

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


if __name__ == "__main__":
    mode_str = "IBM Quantum Hardware" if USE_IBM_QUANTUM else "Local Aer Simulator"
    print(f"=== BB84 Simulation Mode: {mode_str} ===")

    print("\n--- BB84 Simulation Without Eavesdropping ---")
    result = simulate_quantum_channel(has_evedroping=False, use_ibm=USE_IBM_QUANTUM)
    match_index = compare_basis(result["encryption_basis"], result["decryption_basis"])

    print("Match Basis Count:", len(match_index))
    print("Match Indices:", match_index)

    alice_key = bitstring_from_index(result["sent_key"], match_index)
    bob_key = bitstring_from_index(result["received_key"], match_index)

    miss_match = 0
    for i in range(len(alice_key)):
        if alice_key[i] != bob_key[i]:
            miss_match += 1

    print("Number of Miss Match:", miss_match)
    print("Miss Match Rate (QBER):", miss_match / len(match_index) if len(match_index) > 0 else 0)

    print("\n--- BB84 Simulation With Eavesdropping ---")
    result_eve = simulate_quantum_channel(has_evedroping=True, use_ibm=USE_IBM_QUANTUM)
    match_index_eve = compare_basis(result_eve["encryption_basis"], result_eve["decryption_basis"])

    print("Match Basis Count:", len(match_index_eve))
    print("Match Indices:", match_index_eve)

    alice_key_eve = bitstring_from_index(result_eve["sent_key"], match_index_eve)
    bob_key_eve = bitstring_from_index(result_eve["received_key"], match_index_eve)

    miss_match_eve = 0
    for i in range(len(alice_key_eve)):
        if alice_key_eve[i] != bob_key_eve[i]:
            miss_match_eve += 1

    print("Number of Miss Match:", miss_match_eve)
    print("Miss Match Rate (QBER):", miss_match_eve / len(match_index_eve) if len(match_index_eve) > 0 else 0)
