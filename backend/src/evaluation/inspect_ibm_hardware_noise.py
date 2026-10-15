import os
import sys
sys.path.insert(0, "backend/src")
from core.config import settings
from qiskit_ibm_runtime import QiskitRuntimeService
import numpy as np

service = QiskitRuntimeService(channel="ibm_quantum_platform", token=settings.ibm_token)
backend = service.least_busy(operational=True, simulator=False)

print(f"Backend Name: {backend.name}")
print(f"Number of physical qubits: {backend.num_qubits}")
print(f"Processor Type: {backend.processor_type.get('family', 'Heron/Eagle')}")

# Extract sample readout errors and gate errors across physical qubits
readout_errors = []
sx_errors = []

for q in range(min(32, backend.num_qubits)):
    try:
        props = backend.qubit_properties(q)
        # Readout error from target
        meas_err = backend.target['measure'][(q,)].error
        if meas_err is not None:
            readout_errors.append(meas_err)
        sx_err = backend.target['sx'][(q,)].error
        if sx_err is not None:
            sx_errors.append(sx_err)
    except Exception:
        pass

print(f"Physical Qubits Sampled: {len(readout_errors)}")
if readout_errors:
    print(f"Average Readout Error: {np.mean(readout_errors)*100:.2f}% (min: {np.min(readout_errors)*100:.2f}%, max: {np.max(readout_errors)*100:.2f}%)")
if sx_errors:
    print(f"Average Single-Qubit Gate Error: {np.mean(sx_errors)*100:.3f}%")
