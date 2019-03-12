import matplotlib.pyplot as plt
import numpy as np
import argparse
from scipy.io import wavfile


def plot(name):
    print(name)
    samplingFrequency, signalData = wavfile.read(name)
    #flatten into 1D arr
    flat_data = []
    for row in signalData:
        flat_sample = (0.1*row[0] + 0.1*row[1]).astype(np.int16)
        flat_data.append(flat_sample)
    signalData = flat_data
    f_data = np.array(flat_data)
    wavfile.write('test.wav', samplingFrequency, f_data)
    plt.subplot(211)
    plt.title('Spectrogram')
    plt.plot(f_data)
    plt.xlabel('Sample')
    plt.ylabel('Amplitude')

    plt.subplot(212)
    plt.specgram(f_data,Fs=samplingFrequency)
    plt.xlabel('Time')
    plt.ylabel('Frequency')

    plt.show()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--name', type=str, help='file path')
    args = parser.parse_args()
    plot(args.name)


