import os
import random
from math import ceil
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_aer.primitives import SamplerV2 as AerSampler
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit_ibm_runtime.exceptions import IBMInputValueError, IBMError
from qiskit.transpiler import generate_preset_pass_manager

try:
    from core.config import settings
    DEFAULT_IBM_TOKEN = getattr(settings, "ibm_token", "")
except Exception:
    DEFAULT_IBM_TOKEN = os.getenv("IBM_TOKEN", "")

USE_IBM_QUANTUM = os.getenv("USE_IBM_QUANTUM", "false").lower() in ("true", "1", "yes")
IBM_TOKEN = DEFAULT_IBM_TOKEN

_service = None

def get_ibm_service(token: str | None = None) -> QiskitRuntimeService:
    global _service
    if _service is None:
        auth_token = token or IBM_TOKEN
        if not auth_token:
            raise RuntimeError("No IBM Quantum token provided in .env or arguments.")
        try:
            print("[IBM-QUANTUM] Authenticating with IBM Quantum Platform...", flush=True)
            _service = QiskitRuntimeService(channel="ibm_quantum_platform", token=auth_token, instance="auto")
            print("[IBM-QUANTUM] Authentication successful with IBM Quantum Platform.", flush=True)
        except Exception as err:
            raise RuntimeError(
                f"Failed to authenticate with IBM Quantum: {err}. "
                "Please verify your IBM_TOKEN or set use_ibm=False to use the local Aer simulator."
            ) from err
    return _service

# Alias for backward-compatibility if accessed externally
service = None

def random_binary(number_of_bit: int, per_time_bits: int, use_ibm: bool = False):
    times_to_run = ceil(number_of_bit / per_time_bits)

    qc = QuantumCircuit(per_time_bits)

    for i in range(per_time_bits):
        qc.h(i)

    qc.measure_all()

    run_result = run_quantum_circuit(qc, times=times_to_run, use_ibm=use_ibm)

    return ''.join(run_result)[:number_of_bit]

def run_simulation(qc, times = 1):
    print(f"[LOCAL-SIMULATOR] Executing circuit ({qc.num_qubits} qubits, {times} shot(s)) on Qiskit Aer...", flush=True)
    sampler = AerSampler()
    job = sampler.run([qc], shots=times)
    bitstrings = [b[::-1] for b in job.result()[0].data.meas.get_bitstrings()]
    print(f"[LOCAL-SIMULATOR] Aer simulation completed.", flush=True)
    return bitstrings

def run_ibm_hardware(qc, times = 1, token = None):
    print(f"\n[IBM-QUANTUM] ==================================================", flush=True)
    print(f"[IBM-QUANTUM] >>> SUBMITTING QUANTUM TASK TO IBM QUANTUM CLOUD <<<", flush=True)
    runtime_service = get_ibm_service(token)
    print(f"[IBM-QUANTUM] Selecting least busy operational IBM Quantum processor...", flush=True)
    backend = runtime_service.least_busy(operational=True, simulator=False)
    status = backend.status()
    print(f"[IBM-QUANTUM] Selected Backend: {backend.name} ({backend.num_qubits} qubits, pending jobs: {status.pending_jobs})", flush=True)

    print(f"[IBM-QUANTUM] Transpiling circuit ({qc.num_qubits} qubits) to ISA physical architecture...", flush=True)
    pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
    isa_qc = pm.run(qc)
    print(f"[IBM-QUANTUM] Transpilation complete. Circuit depth: {isa_qc.depth()}", flush=True)

    print(f"[IBM-QUANTUM] Submitting job to IBM Quantum cloud queue (shots={times})...", flush=True)
    sampler = Sampler(mode=backend)
    job = sampler.run([isa_qc], shots=times)
    job_id = job.job_id()
    print(f"[IBM-QUANTUM] >>> TASK SUBMITTED SUCCESSFULLY! Job ID: {job_id} <<<", flush=True)
    print(f"[IBM-QUANTUM] Current status: {job.status()}. Waiting for execution on dilution refrigerator...", flush=True)
    result = job.result()
    print(f"[IBM-QUANTUM] Job {job_id} completed successfully!", flush=True)
    print(f"[IBM-QUANTUM] Retrieved {times} shot(s) from real quantum hardware ({backend.name}).", flush=True)
    print(f"[IBM-QUANTUM] ==================================================\n", flush=True)

    return [b[::-1] for b in result[0].data.meas.get_bitstrings()]

def run_quantum_circuit(qc, times = 1, use_ibm: bool = USE_IBM_QUANTUM):
    if use_ibm:
        return run_ibm_hardware(qc, times = times)
    else:
        return run_simulation(qc, times = times)

def simulate_bb84_protocal(key_size = 64, per_time_bits = 64, has_eavesdropping = False, use_ibm: bool = USE_IBM_QUANTUM, channel_noise: float = 0.0):
    effective_noise = channel_noise
    use_real_hardware = os.getenv("USE_REAL_IBM_HARDWARE", "true").lower() in ("true", "1", "yes")
    actual_use_ibm = use_ibm and use_real_hardware

    if use_ibm and not actual_use_ibm and effective_noise == 0.0:
        effective_noise = 0.025

    print(f"\n[QKD-PROTOCOL] ==================================================", flush=True)
    if actual_use_ibm:
        print(f"[QKD-PROTOCOL] Task Execution Target: REAL IBM QUANTUM HARDWARE (Cloud QPU)", flush=True)
    elif use_ibm:
        print(f"[QKD-PROTOCOL] Task Execution Target: IBM QUANTUM SIMULATOR (Realistic Noise: ~2.5% QBER)", flush=True)
    else:
        print(f"[QKD-PROTOCOL] Task Execution Target: LOCAL AER SIMULATOR (Ideal Noise-Free Channel)", flush=True)
    print(f"[QKD-PROTOCOL] Parameters: Key size = {key_size} qubits | Chunk = {per_time_bits} | Eavesdropping = {has_eavesdropping}", flush=True)
    print(f"[QKD-PROTOCOL] ==================================================", flush=True)

    sending_key = random_binary(key_size, per_time_bits, use_ibm=False)
    encryption_basis = random_binary(key_size, per_time_bits, use_ibm=False)
    decryption_basis = random_binary(key_size, per_time_bits, use_ibm=False)

    qc = sending_qubit(sending_key, encryption_basis)

    if has_eavesdropping:
        eavesdropping_basis = random_binary(key_size, per_time_bits, use_ibm=False)
        eavesdropping_result = eavesdropping(qc, eavesdropping_basis, use_ibm=False)

        qc = eavesdropping_result["eavesdropping_copy"]

    qc = receive_qubit(qc, decryption_basis)

    qc.measure_all()

    run_result = run_quantum_circuit(qc, use_ibm=actual_use_ibm)

    receive_key = run_result[0]

    if effective_noise > 0.0:
        receive_key = "".join(
            ('1' if b == '0' else '0') if random.random() < effective_noise else b
            for b in receive_key
        )

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

def sift_bases(alice_basis, bob_basis):
    match_indexes = []

    for i in range(len(alice_basis)):
        if alice_basis[i] == bob_basis[i]:
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

def filter_key_by_basis(key, basis1, basis2):
    match_basis_indexes = sift_bases(basis1, basis2)
    sifted_key = ""

    for i in match_basis_indexes:
        sifted_key += key[i]

    return sifted_key

def QBER(key1, key2):
    key_length = len(key1)
    match_indexes = sift_bases(key1, key2)
    match_count = len(match_indexes)

    return (key_length - match_count) / key_length
