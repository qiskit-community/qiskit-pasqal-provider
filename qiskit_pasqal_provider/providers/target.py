"""Define Pulser-oriented Pasqal target and device wrappers."""

try:
    from enum import StrEnum
except ImportError:
    from qiskit_pasqal_provider.utils import StrEnum  # type: ignore [assignment]

from dataclasses import replace

from pulser.devices import Device, AnalogDevice, DigitalAnalogDevice
from pulser.register import RegisterLayout
from pulser_pasqal import PasqalCloud

from .layouts import PasqalLayout


AVAILABLE_DEVICES = {
    "analog": replace(AnalogDevice, name="PasqalDevice1"),
    "hybrid": replace(DigitalAnalogDevice, name="HybridDevice"),
}


def fetch_remote_device(cloud: PasqalCloud) -> Device:
    """
    Get the QPU device with current valid specs.

    Args:
        cloud: A `PasqalCloud` instance

    Returns:
        A `Device` object for the available QPU
    """

    return cloud.fetch_available_devices()["FRESNEL"]


class PasqalDeviceType(StrEnum):
    """
    StrEnum for available device types
    """

    ANALOG_EMULATOR = "analog"
    HYBRID_EMULATOR = "hybrid"
    FRESNEL_DEVICE = "fresnel"


class PasqalDevice(Device):
    """A wrapper for pulser.device.Device class"""


class PasqalTarget:
    """
    Wrap Pulser device and layout objects for Pasqal backends.

    This class intentionally stays Pulser-oriented instead of inheriting
    ``qiskit.transpiler.Target``. Backends in this provider consume Pulser
    ``Device`` and ``RegisterLayout`` objects directly when building sequences.
    """

    _device: PasqalDevice | Device
    _accepts_new_layouts: bool
    _pre_calibrated_layouts: tuple
    _layout: PasqalLayout | RegisterLayout
    _cloud: PasqalCloud | None

    def __init__(
        self,
        device: PasqalDeviceType | PasqalDevice | Device | str = "analog",
        layout: PasqalLayout | RegisterLayout | None = None,
        cloud: PasqalCloud | None = None,
    ):
        """
        Define the device and register layout used by Pasqal backends.

        Args:
            device (PasqalDeviceType | PasqalDevice | Device | str): Device selector
                or explicit Pulser device instance. Use this with local Pulser devices,
                or pass a `PasqalTarget` originating from integrations such as QRMI.
            layout (PasqalLayout | RegisterLayout, optional): Optional layout to use
                when the selected device does not expose one.
            cloud (PasqalCloud): Optional cloud object that retrieves the available QPU.
                Default to `None`.
        """

        self._cloud = cloud
        self._device = self._get_device(device)
        self._layout = self._get_layout(layout)

    def _get_device(
        self, device: PasqalDeviceType | PasqalDevice | Device | str
    ) -> PasqalDevice | Device:
        """Retrieve the correct device object given a device argument."""

        # if cloud is defined, fetch the device from it
        if self._cloud:
            new_device = fetch_remote_device(self._cloud)
            self._accepts_new_layouts = new_device.accepts_new_layouts
            self._pre_calibrated_layouts = new_device.pre_calibrated_layouts
            return new_device

        if isinstance(device, PasqalDeviceType | str):
            new_device = AVAILABLE_DEVICES[device]
            self._accepts_new_layouts = new_device.accepts_new_layouts
            self._pre_calibrated_layouts = new_device.pre_calibrated_layouts
            return new_device

        if isinstance(device, PasqalDevice | Device):
            self._accepts_new_layouts = device.accepts_new_layouts
            self._pre_calibrated_layouts = device.pre_calibrated_layouts
            return device

        raise TypeError(f"'{device.name}' of type {type(device)} is not supported")

    def _get_layout(
        self, layout: PasqalLayout | RegisterLayout | None
    ) -> PasqalLayout | RegisterLayout:
        """
        Based on device definitions and provided layout argument, sets the
        layout for PasqalDevice instance.

        Args:
            layout (PasqalLayout, None): Optional argument to define the device
                layout. Default to `None`.

        Returns:
            A valid PasqalLayout instance given the device attribute
        """

        if layout is None:
            if self._pre_calibrated_layouts:
                return self._pre_calibrated_layouts[0]

            raise ValueError(
                f"a layout needs to be provided for device '{self.device.name}'"
            )

        if self._accepts_new_layouts:

            if self._pre_calibrated_layouts:

                if self.device.is_calibrated_layout(layout):  # type: ignore [arg-type]
                    return layout

                raise ValueError("layout does not match the pre-calibrated layouts.")

            return layout

        raise ValueError(f"device '{self.device.name}' does not accept new layouts")

    @property
    def device(self) -> PasqalDevice | Device:
        """device attribute"""
        return self._device

    @property
    def layout(self) -> PasqalLayout | RegisterLayout:
        """layout attribute"""
        return self._layout
