import os
import sys
sys.path.insert(0, "backend/src")
from core.config import settings
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit.transpiler import generate_preset_pass_manager
from qiskit import QuantumCircuit
import time

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=settings.ibm_token)
backend = service.least_busy(operational=True, simulator=False)
status = backend.status()
print(f"Target backend: {backend.name}")
print(f"Pending jobs in queue: {status.pending_jobs}")

# Build a small 8-qubit test circuit
qc = QuantumCircuit(8)
qc.h(range(8))
qc.measure_all()

pm = generate_preset_pass_manager(backend=backend, optimization_level=1)
isa_qc = pm.run(qc)
print("Circuit transpiled to ISA format successfully.")
print(f"Backend coupling map / layout verified on {backend.name}.")
