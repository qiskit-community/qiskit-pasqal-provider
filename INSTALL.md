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

## Installing local emulators

Note that since the analog paradigm is different from the digital paradigm usually programmed with Qiskit, this provider cannot use the normal Qiskit numerical simulators.
The [QuTiP](https://qutip.org/) based backend is available through the `qutip` extra:
```bash
python3 -m pip install qiskit-pasqal-provider[qutip]
```

For running larger local simulations, [emu-mps](https://pasqal-io.github.io/emulators/latest/emu_mps/) is also available.
Install both local emulator backends without OpenQASM3 transport dependencies with:
```bash
python3 -m pip install qiskit-pasqal-provider[emulators]
```

OpenQASM3 transport helpers are available through the `qasm3` extra:
```bash
python3 -m pip install qiskit-pasqal-provider[qasm3]
```

Install all optional dependencies with:
```bash
python3 -m pip install qiskit-pasqal-provider[all]
```
