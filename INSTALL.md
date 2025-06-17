# Qiskit Pasqal Provider Installation Guide


## Setting up Python Environment

We recommend using a virtual environment, for which there are many alternatives.
Most widely available is using the built in `venv`.

```bash
python3 -m venv qpp-venv
source qpp-venv/bin/activate
```


## Installing Qiskit Pasqal Provider

Install the project from PyPi:
```bash
python3 -m pip install qiskit-pasqal-provider
```

## Installing tensor network emulators

Note that since the analog paradigm is different from the digital paradigm usually programmed with Qiskit, this provider cannot use the normal Qiskit numerical simulators.
Built in we support a [QuTiP](https://qutip.org/) based backend, known as `pulser-simulator` in the Pasqal's Pulser.
For running larger local simulations we recommend installing [emu-mps](https://pasqal-io.github.io/emulators/latest/emu_mps/), a tensor network backend.
You can install this together with qiskit-pasqal-provider as:
```bash
python3 -m pip install qiskit-pasqal-provider[mps]
```
