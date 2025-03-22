import serial
import struct
import threading

HEARTBEAT = "heartbeat"
RTC_TIME = "rtc_time"
CHANNEL_LIVE_DATA = "channel_live_data"
CHANNEL_CONFIG = "channel_config"
OPTIC_CONNECTION = "optic_connection"
DEVICE_RECORDING_STATE = "device_recording_state"

HEARTBEAT_BEAT = 0x00

STRUCT_FORMATS = {
    HEARTBEAT: "B",  # uint8_t beat = 0x00
    RTC_TIME: "B H 5B",  # struct_id (uint8), year (uint16), month, day, hour, min, sec (5x uint8)
    CHANNEL_LIVE_DATA: "B B H 5B 8B",  # struct_id (uint8), rtc_struct, 8x uint8 channels
    CHANNEL_CONFIG: "B 7B",  # struct_id (uint8), 7x uint8_t values
    OPTIC_CONNECTION: "B B",  # struct_id (uint8), recording_state (uint8)
    DEVICE_RECORDING_STATE: "B B"  # struct_id (uint8), optic_state (uint8)
}

def send_struct(ser, struct_type, *data):
    if struct_type not in STRUCT_FORMATS:
        print(f"Error: Unknown struct type {struct_type}")
        return False

    fmt = STRUCT_FORMATS[struct_type]
    try:
        packed_data = struct.pack(fmt, *data)
        ser.write(packed_data)
        ser.flush()
        return True
    except struct.error as e:
        print(f"Error packing data for struct type {struct_type}: {e}")
        return False


# def receive_struct(ser, struct_type):
#     fmt = STRUCT_FORMATS[struct_type]
#     size = struct_size(fmt)
#     raw_data = ser.read(size)
#     if len(raw_data) != size:
#         print("Error: Incomplete data received")
#         return None
#     return struct.unpack(fmt, raw_data)

# def parse_heartbeat(ser):
#     beat = receive_struct(ser, "heartbeat")[0]
#     return "heartbeat is beating"


# STRUCT_PARSERS = {
#     0x00: parse_heartbeat,
# }

# Open serial connection

# def polling_thread():
#     while True:
#         struct_id = ser.read(1)
#         if not struct_id:
#             continue
#         struct_id = struct.unpack("B", struct_id)[0]
#
#         # if struct_id in STRUCT_PARSERS:
#         #     parsed_data = STRUCT_PARSERS[struct_id](ser)
#         #     print(f"Received struct {struct_id}: {parsed_data}")
#         # else:
#         #     print(f"Unknown struct ID: {struct_id}")


# Start polling in a separate thread
# thread = threading.Thread(target=polling_thread, daemon=True)
# thread.start()

def send_heartbeat(ser):
    send_struct(ser, HEARTBEAT, HEARTBEAT_BEAT)

def heartbeat_timer(ser):
    send_heartbeat(ser)
    threading.Timer(0.5, heartbeat_timer, args=[ser]).start()  # Re-call itself every 500ms


if __name__ == "__main__":
    ser_handle = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

    # Start the heartbeat timer
    heartbeat_timer(ser_handle)