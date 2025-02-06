"""Defines the Pasqal Target and Device classes"""

from enum import StrEnum
from dataclasses import replace

from pulser.devices import Device, AnalogDevice, DigitalAnalogDevice
from pulser.devices._device_datacls import BaseDevice
from pulser.register import RegisterLayout

from .pasqal_layout import PasqalLayout

# rethink about the names
AVAILABLE_DEVICES = {
    "pasqal_device": replace(AnalogDevice, name="PasqalDevice1"),
    "hybrid": replace(DigitalAnalogDevice, name="HybridDevice"),
}


class PasqalDeviceType(StrEnum):
    """
    StrEnum for available device types
    """

    PASQAL_DEVICE = "pasqal_device"
    HYBRID = "hybrid"


class PasqalDevice(Device):
    """A wrapper for pulser.device.Device class"""


class PasqalTarget:
    """
    `PasqalDevice` class defines `Pulser`'s device and register layouts
    to be used by `PasqalBackend` instances.
    """

    _device: PasqalDevice | BaseDevice
    _accepts_new_layouts: bool
    _pre_calibrated_layouts: tuple
    _layout: PasqalLayout | RegisterLayout

    def __init__(
        self,
        device: PasqalDeviceType | PasqalDevice | BaseDevice | str,
        layout: PasqalLayout | RegisterLayout | None = None,
    ):
        """
        PasqalDevice constructor defines device and register layout used by
        PasqalBackend instance.

        Args:
            device (PasqalDeviceType, Device, str): `PasqalDeviceType` value or string
                with the name of the device when the device is known; Use `Device` when
                providing custom device instance.
            layout (PasqalLayout, None): Optional parameter to define the layout of the
                device, if the device does not provide one. It will try to retrieve the
                layout from the device, unless it provides `PasqalLayout` instance. If
                `None` is provided and no layout is found, an error raises. Default to
                `None`.
        """

        self._device = self._get_device(device)
        self._layout = self._get_layout(layout)

    def _get_device(
        self, device: PasqalDeviceType | PasqalDevice | BaseDevice | str
    ) -> PasqalDevice | BaseDevice:
        if isinstance(device, PasqalDeviceType | str):
            new_device = AVAILABLE_DEVICES[device]
            self._accepts_new_layouts = new_device.accepts_new_layouts
            self._pre_calibrated_layouts = new_device.pre_calibrated_layouts
            return new_device

        if isinstance(device, PasqalDevice | Device):
            self._accepts_new_layouts = device.accepts_new_layouts
            self._pre_calibrated_layouts = device.pre_calibrated_layouts
            return device

        if isinstance(device, BaseDevice):
            self._accepts_new_layouts = True
            self._pre_calibrated_layouts = ()
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

                if self.device.is_calibrated_layout(layout):  # type: ignore [attr-defined]
                    return layout

                raise ValueError("layout does not match the pre-calibrated layouts.")

            return layout

        raise ValueError(f"device '{self.device.name}' does not accept new layouts")

    @property
    def device(self) -> PasqalDevice | BaseDevice:
        """device attribute"""
        return self._device

    @property
    def layout(self) -> PasqalLayout | RegisterLayout:
        """layout attribute"""
        return self._layout
