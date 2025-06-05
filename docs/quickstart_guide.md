# Quickstart Guide

## Installation

First you have to do the [Installation](INSTALL.md).
```bash
python3 -m pip install qiskit-pasqal-provider
```

## Usage

The Qiskit Pasqal Provider works with regular Qiskit functions like the `SamplerV2`.
What is required is the use of two classes found in this project, the `PasqalProvider` and:
```python
HamiltonianGate(amplitude=ampl, detuning=det, phase=phase, coords=coords)
```

Let us see a simple example

```python
from qiskit.circuit import QuantumCircuit

from qiskit_pasqal_provider.providers.gate import (HamiltonianGate,
                                                   InterpolatePoints)
from qiskit_pasqal_provider.providers.provider import PasqalProvider
from qiskit_pasqal_provider.providers.sampler import Sampler

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
sampler_qutip = Sampler(backend_qutip)
results_qutip = sampler_qutip.run([qc], shots=1000).result()

print(results_qutip[0].data.counts)
```
```bash
Counter({'100110': 139, '010001': 127, '010100': 111, '001000': 92, '100001': 92, ... })
```
