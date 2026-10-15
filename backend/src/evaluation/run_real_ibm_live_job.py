"""
Live Execution on Real IBM Quantum Hardware (ibm_kingston, 156-qubit Heron processor)
Submits a real QKD BB84 quantum circuit to the IBM Quantum cloud QPU and retrieves live results.
"""

import os
import sys
sys.path.insert(0, "backend/src")
from core.config import settings
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import generate_preset_pass_manager
from qiskit import QuantumCircuit
import random

print("Connecting to IBM Quantum Platform...")
service = QiskitRuntimeService(channel="ibm_quantum_platform", token=settings.ibm_token)
backend = service.least_busy(operational=True, simulator=False)
print(f"Selected least busy backend: {backend.name} ({backend.num_qubits} qubits, Heron architecture)")

# Send 24 qubits (voting payload for 'VT3')
n_qubits = 24
random.seed(42)
alice_bits = [random.choice(['0', '1']) for _ in range(n_qubits)]
alice_bases = [random.choice(['0', '1']) for _ in range(n_qubits)]
bob_bases = [random.choice(['0', '1']) for _ in range(n_qubits)]

# Build circuit
qc = QuantumCircuit(n_qubits)
# Alice encodes
for i in range(n_qubits):
    if alice_bits[i] == '1':
        qc.x(i)
    if alice_bases[i] == '1':
        qc.h(i)

# Bob measures
for i in range(n_qubits):
    if bob_bases[i] == '1':
        qc.h(i)

qc.measure_all()

print("Transpiling circuit to physical ISA layout on IBM QPU...")
pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_qc = pm.run(qc)

print("Submitting job to IBM Quantum cloud QPU queue (shots=100)...")
sampler = Sampler(mode=backend)
job = sampler.run([isa_qc], shots=100)
job_id = job.job_id()
print(f"Job successfully submitted! Job ID: {job_id}")
print(f"Current status: {job.status()}")
print("Waiting for QPU execution on dilution refrigerator...")
result = job.result()
print("Job execution complete on real IBM Quantum Hardware!")

# Retrieve raw bitstrings
bitstrings = [b[::-1] for b in result[0].data.meas.get_bitstrings()]
print(f"Retrieved {len(bitstrings)} shots from real QPU.")

# Compute QBER on sifted key across matching bases
sifted_indices = [i for i in range(n_qubits) if alice_bases[i] == bob_bases[i]]
print(f"Sifted key indices (bases matched): {len(sifted_indices)} bits out of {n_qubits}")

trial_qbers = []
for bs in bitstrings:
    errors = sum(1 for i in sifted_indices if bs[i] != alice_bits[i])
    trial_qbers.append((errors / len(sifted_indices)) * 100.0)

mean_real_qber = sum(trial_qbers) / len(trial_qbers)
print(f"Real IBM Quantum Hardware Mean QBER: {mean_real_qber:.2f}%")
print(f"Job ID: {job_id}")
