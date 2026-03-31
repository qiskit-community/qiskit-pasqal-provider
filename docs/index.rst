#####################################
Qiskit Pasqal Provider documentation
#####################################

.. toctree::
  :hidden:

  Home <self>

.. toctree::
  :maxdepth: 1
  :hidden:

  Tutorials <tutorials/index>
  API References <apidocs/index>

.. Hiding - Indices and tables
   :ref:`genindex`
   :ref:`modindex`
   :ref:`search`

This project contains the appropriate abstraction to program `Pasqal <https://pasqal.com>`_'s analog neutral atom QPUs from Qiskit.

We encourage the user to check out specialized resources, such as the `Pulser documentation <https://pulser.readthedocs.io/en/stable/>`_, to discover how to best program analog neutral atom QPUs.

To target Pasqal's QPUs or cloud based emulators, sign up for `Pasqal cloud <https://www.pasqal.com/solutions/cloud/>`_.


Installation
##############

Qiskit Pasqal Provider can be installed with pip
``
python3 -m pip install qiskit-pasqal-provider
``

Usage
######

The Qiskit Pasqal Provider works with regular Qiskit functions like the ``SamplerV2``.
What is required is the use of two classes found in this project, the ``PasqalProvider`` and:

.. code-block:: python

  HamiltonianGate(amplitude=ampl, detuning=det, phase=phase, coords=coords)

Qiskit Pasqal Provider supports both Qiskit 1.x and Qiskit 2.x.

``SamplerV2.run(...)`` accepts exactly one pub per call.
Use ``[qc]`` or ``[(qc, parameter_values)]``.

Local emulator example (qutip)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python3

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

    # Counter({'100110': 139, '010001': 127, '010100': 111, '001000': 92, '100001': 92, ... })

Parameterized example (single pub)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python3

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

Remote cloud emulator example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python3

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

QRMI
####

To run this provider through a workload manager (for example in HPC environments),
see `QRMI <https://github.com/qiskit-community/qrmi>`_.
QRMI provides queue and scheduler integrations around Qiskit workloads, and can be
used with this provider in those environments.
