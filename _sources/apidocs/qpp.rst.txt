.. automodule:: qiskit_pasqal_provider.providers
   :no-members:
   :no-inherited-members:
   :no-special-members:

.. _circuit-compile-time-parameters:

Compile-time parameters
-----------------------

Qiskit Pasqal Provider does not provide a compile-time-parameter feature.
This section exists only to resolve an inherited Qiskit API reference label.

The provider supports binding ``qiskit.circuit.Parameter`` and
``qiskit.circuit.ParameterExpression`` values at run time through
``SamplerV2.run([(circuit, parameter_values)])``.
This includes scalar phase expressions and waveform duration expressions.

For the Qiskit definition of compile-time parameters, see
`Qiskit circuit parameters documentation <https://docs.quantum.ibm.com/guides/parameterized-circuits>`_.
