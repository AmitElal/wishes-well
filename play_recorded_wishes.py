import os
import random

import pyaudio
import wave
import sys

# need to implement:
# add voice changer to wishes for burners privacy
pa = pyaudio.PyAudio()

CHUNK = 1024

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_SIZE = pa.get_sample_size(FORMAT)
SAMPLE_WIDTH = 2
RATE = 44100

def print_input_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    for i in range(0, num_devices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))


print_input_devices()

stream = pa.open(format=pa.get_format_from_width(SAMPLE_WIDTH),
                 channels=CHANNELS,
                 rate=RATE,
                 output=True,
                 output_device_index=5)


def play_insult():
    directory = "C://Users/Amit/PycharmProjects/wishes-well/wishes_recordings"
    # gets random file from selected directory
    file = random.choice(os.listdir(directory))
    file_to_play = "wishes_recordings/" + str(file)

    wf = wave.open(file_to_play)

    data = wf.readframes(CHUNK)

    while len(data):
        stream.write(data)
        data = wf.readframes(CHUNK)


print_input_devices()

while True:
    play_insult()

stream.stop_stream()
stream.close()
pa.terminate()

