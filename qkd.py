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

    backend = service.least_busy(operational = True, simulator = False)

    pm = generate_preset_pass_manager(backend = backend, optimization_level = 1)
    isa_qc = pm.run(qc)

    sampler = Sampler(mode = backend)
    job = sampler.run([isa_qc], shots = ceil(number_of_bit / generate_bitcount))

    result = job.result()
    bitstrings = result[0].data.meas.get_bitstrings()
    return ''.join(bitstrings)

random_binary(512)
