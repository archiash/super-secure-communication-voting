import os
import sys
sys.path.insert(0, "backend/src")
from core.config import settings
from qiskit_ibm_runtime import QiskitRuntimeService

print(f"Token present: {bool(settings.ibm_token)}")
try:
    service = QiskitRuntimeService(channel="ibm_quantum_platform", token=settings.ibm_token)
    backends = service.backends()
    print("Connected successfully! Available backends:")
    for b in backends:
        status = b.status()
        print(f" - {b.name}: operational={status.operational}, pending_jobs={status.pending_jobs}, num_qubits={b.num_qubits}")
except Exception as e:
    print(f"Error connecting to IBM Quantum: {e}")
