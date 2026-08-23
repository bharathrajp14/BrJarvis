import sys

if __name__ in sys.modules:
    sys.modules.setdefault("mobile", sys.modules[__name__])

from .device_controller import AndroidDeviceController
from .gateway import DeviceGateway, PairedDevice, get_device_gateway
from .protocol import AccessibilityNode, DeviceState, MobileMessage, MobileMessageType

__all__ = [
    "MobileMessage",
    "MobileMessageType",
    "AccessibilityNode",
    "DeviceState",
    "get_device_gateway",
    "DeviceGateway",
    "PairedDevice",
    "AndroidDeviceController",
]
