import sys
import numpy as np
import serial

# ── Constants ──
SAMPLE_RATE = 16000
MIC_SPACING = 0.226          # meters, outer mic pair
SPEED_OF_SOUND = 343         # m/s
MAX_TAU = MIC_SPACING / SPEED_OF_SOUND
BLOCK_SIZE = 128             # frames per block
BLOCK_BYTES = BLOCK_SIZE * 4 * 4  # 2048 bytes

# ── Serial to Arduino ──
SERIAL_PORT = '/dev/cu.usbmodem1201'
BAUD_RATE = 115200
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE)
arduino.reset_input_buffer()
arduino.reset_output_buffer()

# ── GCC-PHAT ──
# Adapted from https://github.com/xiongyihui/tdoa/blob/master/gcc_phat.py
# Copyright (c) 2017 Yihui Xiong, Apache License 2.0
def gcc_phat(sig, refsig):
    n = len(sig) + len(refsig)
    SIG = np.fft.rfft(sig, n=n)
    REFSIG = np.fft.rfft(refsig, n=n)
    R = SIG * np.conj(REFSIG)
    R /= np.abs(R) + 1e-10
    cc = np.fft.irfft(R)
    max_shift = int(SAMPLE_RATE * MAX_TAU) + 1
    cc = np.concatenate((cc[-max_shift:], cc[:max_shift + 1]))
    shift = np.argmax(cc) - max_shift
    return shift / SAMPLE_RATE

THRESHOLD = 15000000
counter = 0
last_errors = []

print("Listening...", file=sys.stderr)

# ── Main loop ──
while True:
    # Read one block of audio from C program
    raw = sys.stdin.buffer.read(BLOCK_BYTES)
    if len(raw) < BLOCK_BYTES:
        break

    # Parse into 4-channel array
    data = np.frombuffer(raw, dtype=np.int32).reshape(-1, 4)
    mic1 = data[:, 0].astype(np.float64)
    mic4 = data[:, 3].astype(np.float64)

    # Energy gate: skip quiet blocks
    rms = np.sqrt(np.mean(mic1**2))
    counter += 1

    if rms < THRESHOLD:
        last_errors.clear()
        arduino.write(b'0\n')
        if counter % 100 == 0:
            print(f"quiet  rms: {rms:.0f}", file=sys.stderr)
        continue

    # GCC-PHAT: find time delay between outer mics
    tau = gcc_phat(mic1, mic4)

    # Convert delay to angle error (degrees off-center)
    ratio = np.clip((tau * SPEED_OF_SOUND) / MIC_SPACING, -1, 1)

    # Reject edge hits — unreliable readings near physical limits
    if abs(ratio) > 0.9:
        continue

    error = np.degrees(np.arcsin(ratio))
    last_errors.append(error)

    # Only send when 3 consecutive readings agree within 15 degrees
    if len(last_errors) >= 3:
        recent = last_errors[-3:]
        spread = max(recent) - min(recent)
        if spread < 15:
            avg_error = sum(recent) / len(recent)
            arduino.write(f'{int(avg_error)}\n'.encode())
            print(f"SEND error: {avg_error:.1f}  rms: {rms:.0f}", file=sys.stderr)
            last_errors.clear()
        elif len(last_errors) > 5:
            last_errors.pop(0)

    print(f"raw error: {error:.1f}  rms: {rms:.0f}", file=sys.stderr)