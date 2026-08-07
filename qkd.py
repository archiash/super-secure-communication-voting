from math import ceil
from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import generate_preset_pass_manager

QiskitRuntimeService.save_account(
    channel = "ibm_quantum_platform",
    token = "_-wHEwqqjche7HiBEujkF56DE3mow3AjlamiKgvG873s",
    set_as_default = True,
    overwrite = True
)

service = QiskitRuntimeService()

generate_bitcount = 128

def random_binary(number_of_bit: int):
    qc = QuantumCircuit(generate_bitcount)

    for i in range(generate_bitcount):
        qc.h(i)

    qc.measure_all()

    result = run_quantum_circuit(qc, times = ceil(number_of_bit / generate_bitcount))

    return ''.join(result)


def run_quantum_circuit(qc, times = 1):
    backend = service.least_busy(operational = True, simulator = False)

    pm = generate_preset_pass_manager(backend = backend, optimization_level = 1)
    isa_qc = pm.run(qc)

    sampler = Sampler(mode = backend)
    job = sampler.run([isa_qc], shots = times)

    result = job.result()
    bitstrings = result[0].data.meas.get_bitstrings()

    return bitstrings

def simulate_quantum_channel(has_evedroping = False):
    sending_key = random_binary(128)
    encryption_basis = random_binary(128)
    decryption_basis = random_binary(128)

    qc = receive_qubit(sending_qubit(sending_key, encryption_basis), decryption_basis)

    if has_evedroping:
        evedroping_basis = random_binary(128)
        evedroping_result = evedroping(qc, evedroping_basis)

        qc = evedroping_result["qc"]

    qc.measure_all()

    run_result = run_quantum_circuit(qc)

    receive_key = ''.join(run_result)

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

    return 

def evedroping(qc, basis):
    for i in range(len(basis)):
        if data[i] == '1':
            qc.x(i)
    
    qc.measure_all()

    run_result = run_quantum_circuit(qc)

    receive_key = ''.join(run_result)
    
    fake_qc = QuantumCircuit(len(basis))
    
    for i in range(len(basis)):
        if received_key[i] == '1':
            fake_qc.x(i)

    for i in range(len(basis)):
        if basis[i] == '1':
            fake_qc.x(i)

    return {
        "fake_qc" : fake_qc,
        "evedrop_key" : received_key
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

def compare_basis(encrypt_basis, decrypt_baqsis):
    match_index = []

    for i in range(len(sent_key)):
        if encrypt_basis[i] == decrypt_baqsis[i]:
            match_index.append(i)

    return match_index

def receive_qubit(qc, basis):
    for i in range(len(basis)):
        if basis[i] == '1':
            qc.h(i)

    return qc

result = simulate_quantum_channel(True)
print(result)
