import serial
import struct
import threading

HEARTBEAT = "heartbeat"
RTC_TIME = "rtc_time"
CHANNEL_LIVE_DATA = "channel_live_data"
CHANNEL_CONFIG = "channel_config"
OPTIC_CONNECTION = "optic_connection"
DEVICE_RECORDING_STATE = "device_recording_state"

STRUCT_FORMATS = {
    HEARTBEAT: "B",  # uint8_t
    RTC_TIME: "B H 5B",  # struct_id (uint8), year (uint16), month, day, hour, min, sec (5x uint8)
    CHANNEL_LIVE_DATA: "B B H 5B 8B",  # struct_id (uint8), rtc_struct, 8x uint8 channels
    CHANNEL_CONFIG: "B 7B",  # struct_id (uint8), 7x uint8_t values
    OPTIC_CONNECTION: "B B",  # struct_id (uint8), recording_state (uint8)
    DEVICE_RECORDING_STATE: "B B"  # struct_id (uint8), optic_state (uint8)
}
