# Quickstart Guide

## Installation

First you have to do the [Installation](../INSTALL.md).
```bash
python3 -m pip install qiskit-pasqal-provider[qutip]
```

## Usage

The Qiskit Pasqal Provider works with regular Qiskit functions like the `SamplerV2`.
What is required is the use of two classes found in this project, the `PasqalProvider` and:
```python
HamiltonianGate(amplitude=ampl, detuning=det, phase=phase, coords=coords)
```

Qiskit Pasqal Provider supports both Qiskit 1.x and Qiskit 2.x.

`SamplerV2.run(...)` accepts exactly one pub per call.
For example, use `[qc]` or `[(qc, parameter_values)]`.

### Local emulator example (`qutip`)

```python
from qiskit.circuit import QuantumCircuit

from qiskit_pasqal_provider.providers.gate import (HamiltonianGate,
                                                   InterpolatePoints)
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.sampler import SamplerV2

# We define the coordinates of the atoms, 6 in total.
coords = [[0, 0], [3, 5.2], [6, 0], [9, -5.2], [9, 5.2], [12, 0]]

# With a blockade radius of 8.7
blockade_radius = 8.7

# Calculate interaction strength between nearest-neighbours
interaction = 5420158.53 / blockade_radius**6

# Set up an adiabatic pulse,
# This pulse ramps from up 0 -> 4, stays constant, and ramps down again during the times
times = [0, 0.2, 0.8, 1]
ampl = InterpolatePoints(values=[0, 4, 4, 0], times=times)
det = InterpolatePoints(
    values=[-10, -10, interaction / 2, interaction / 2],
    times=times,
)
phase = 0.0

# analog gate
gate = HamiltonianGate(ampl, det, phase, coords, grid_transform="triangular")

# Qiskit circuit with analog gate
qc = QuantumCircuit(len(coords))
qc.append(gate, qc.qubits)

provider_qutip = PasqalProvider()
backend_qutip = provider_qutip.get_backend("qutip")
sampler_qutip = SamplerV2(backend_qutip)
results_qutip = sampler_qutip.run([qc], shots=1000).result()

print(results_qutip[0].data.counts)
```
```bash
Counter({'100110': 139, '010001': 127, '010100': 111, '001000': 92, '100001': 92, ... })
```

### Parameterized example (single pub)

`qiskit` `Parameter` and `ParameterExpression` are supported for parameterized runs.
This includes scalar phase expressions and waveform duration expressions.

```python
from qiskit.circuit import Parameter, QuantumCircuit

from qiskit_pasqal_provider.providers.gate import HamiltonianGate, InterpolatePoints
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.sampler import SamplerV2

coords = [[0, 0], [3, 5.2], [6, 0], [9, -5.2], [9, 5.2], [12, 0]]
times = [0, 0.2, 0.8, 1]
amplitude = InterpolatePoints(values=[0, 4, 4, 0], times=times)
detuning = InterpolatePoints(values=[-10, -10, -5, -5], times=times)
phase = Parameter("phase")

gate = HamiltonianGate(amplitude, detuning, phase, coords, grid_transform="triangular")

qc = QuantumCircuit(len(coords))
qc.append(gate, qc.qubits)

provider = PasqalProvider()
sampler = SamplerV2(provider.get_backend("qutip"))

# Exactly one pub: [(circuit, parameter_values)]
result = sampler.run([(qc, {phase: 0.2})], shots=500).result()
print(result[0].data.counts)
```

### Remote cloud emulator example

```python
import os

from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.sampler import SamplerV2
from qiskit_pasqal_provider.utils import RemoteConfig

# Use your Pasqal Cloud credentials
remote_config = RemoteConfig(
    username=os.environ["PASQAL_USERNAME"],
    password=os.environ["PASQAL_PASSWORD"],
    project_id=os.environ["PASQAL_PROJECT_ID"],
)

provider = PasqalProvider(remote_config=remote_config)
backend = provider.get_backend("remote-emu-fresnel")
sampler = SamplerV2(backend)

# Reuse `qc` from the local example (or build a new circuit in the same way).
job = sampler.run([qc], shots=1000)
print(job.job_id())
print(job.status())
print(job.result()[0].data.counts)
```

### Choosing the register layout

On a QPU, atoms can only sit on the traps of a register layout, and every new layout
has to be calibrated first, which takes time. Reusing one of the device's pre-calibrated
layouts avoids that. See Pulser's
[Register Layouts & Mappable Registers](https://pulser.readthedocs.io/en/stable/tutorials/reg_layouts.html)
tutorial for the details.

By default, the provider places the atoms on the device's first pre-calibrated layout
when they fit on its traps (up to a translation), and otherwise generates a new layout
if the device accepts one. To choose the layout yourself, pick atom coordinates from its
traps and pass it through a `PasqalTarget`:

```python
from pasqal_cloud import PasqalCloudConnection

from qiskit_pasqal_provider.providers.target import PasqalTarget

cloud = PasqalCloudConnection(
    username=remote_config.username,
    password=remote_config.password,
    project_id=remote_config.project_id,
)
device = cloud.fetch_available_devices()["FRESNEL"]
layout = device.pre_calibrated_layouts[0]

# place the atoms on traps 0-3 of the chosen layout
coords = [list(c) for c in layout.define_register(0, 1, 2, 3).qubits.values()]
qc = QuantumCircuit(len(coords))
qc.append(HamiltonianGate(ampl, det, phase, coords), qc.qubits)

target = PasqalTarget(device=device, layout=layout)
sampler = SamplerV2(provider.get_backend("fresnel", target=target))
```

### QRMI integration

To run this provider through a workload manager (for example in HPC environments),
see [QRMI](https://github.com/qiskit-community/qrmi).
QRMI provides queue and scheduler integrations around Qiskit workloads, and can be
used with this provider in those environments.


### OpenQASM3-Compatible Transport Serialization

For serializing Qiskit programs with the custom Pasqal analog gate, we use an OpenQASM3-compatible transport format.
Since we have a custom gate, we need custom serialize and deserialize methods.
Install `qiskit-pasqal-provider[qasm3]` to use these helpers.

```python
from qiskit.circuit import QuantumCircuit
from qiskit_pasqal_provider.providers.gate import (
    HamiltonianGate,
    InterpolatePoints,
    dumps_qpp_openqasm3,
    loads_qpp_openqasm3,
)

coords = [[0, 0], [3, 5.2], [6, 0], [9, -5.2], [9, 5.2], [12, 0]]
times = [0, 0.2, 0.8, 1]
ampl = InterpolatePoints(values=[0, 4, 4, 0], times=times)
det = InterpolatePoints(values=[-10, -10, -5, -5], times=times)

qc = QuantumCircuit(len(coords))
qc.append(HamiltonianGate(ampl, det, 0.0, coords), qc.qubits)

program = dumps_qpp_openqasm3(qc)
restored = loads_qpp_openqasm3(program)
```
