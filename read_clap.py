import sys
import struct
import numpy as np
import serial
from scipy.signal import butter, filtfilt

arduino = serial.Serial('/dev/cu.usbmodem1301', 9600)

smoothed_angle = 0.0
alpha = 0.3
num, den = butter(2, [300, 3000], btype='band', fs=16000)
threshold = 12000000

def spectral_flatness(signal, fs):
    spectrum = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), d=1/fs)
    mask = (freqs >= 1500) & (freqs <= 5000)
    band = spectrum[mask] + 1e-10
    geo = np.exp(np.mean(np.log(band)))
    arith = np.mean(band)
    return geo / arith

def gcc_phat(sig, refsig, fs=1, max_tau=None, interp=16):
    '''
    This function computes the offset between the signal sig and the reference signal refsig
    using the Generalized Cross Correlation - Phase Transform (GCC-PHAT)method.
    '''
    
    # make sure the length for the FFT is larger or equal than len(sig) + len(refsig)
    n = sig.shape[0] + refsig.shape[0]

    # Generalized Cross Correlation Phase Transform
    SIG = np.fft.rfft(sig, n=n)
    REFSIG = np.fft.rfft(refsig, n=n)
    R = SIG * np.conj(REFSIG)

    cc = np.fft.irfft(R / np.abs(R), n=(interp * n))

    max_shift = int(interp * n / 2)
    if max_tau:
        max_shift = np.minimum(int(interp * fs * max_tau), max_shift)

    cc = np.concatenate((cc[-max_shift:], cc[:max_shift+1]))

    # find max cross correlation index
    shift = np.argmax(cc) - max_shift

    # Sometimes, there is a 180-degree phase difference between the two microphones.
    # shift = np.argmax(np.abs(cc)) - max_shift

    tau = shift / float(interp * fs)
    
    return tau, cc

while True:
    raw = sys.stdin.buffer.read(8192)
    if len(raw) < 8192:
        break
    data = np.frombuffer(raw, dtype=np.int32)
    data = data.reshape(-1,4)
    mic1 = data[:, 0].astype(np.float64)
    mic4 = data[:, 3].astype(np.float64)    

    rms_m1 = np.sqrt(np.mean(mic1**2))
    if rms_m1 < threshold:
        continue

    flatness = spectral_flatness(mic1, 16000)
    if flatness < 0.3:
        continue

    tau, _ = gcc_phat(mic1, mic4, fs=16000, max_tau=0.000659)
    ratio = np.clip((tau * 343) / 0.226, -1, 1)
    angle = np.degrees(np.arcsin(ratio))
    smoothed_angle = alpha * angle + (1 - alpha) * smoothed_angle

    print(f"angle: {smoothed_angle:.1f}")
    arduino.write(f'{smoothed_angle}\n'.encode())
