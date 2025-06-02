"""Defines the Pasqal Target and Device classes"""

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
    `PasqalDevice` class defines `Pulser`'s device and register layouts
    to be used by `PasqalBackend` instances.
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
        PasqalDevice constructor defines device and register layout used by
        PasqalBackend instance.

        Args:
            device (PasqalDeviceType, Device, str): `PasqalDeviceType` value or string
                with the name of the device when the device is known; Use `PasqalDevice`
                when providing custom device instance. Default to `"analog"`.
            layout (PasqalLayout, None): Optional parameter to define the layout of the
                device, if the device does not provide one. It will try to retrieve the
                layout from the device, unless it provides `PasqalLayout` instance. If
                `None` is provided and no layout is found, an error raises. Default to
                `None`.
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
