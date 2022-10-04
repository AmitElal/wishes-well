import os
import random
import time
import wave

import numpy
import pyaudio
from scipy.signal import lfilter

import spl_lib as spl

# PyAudio variables
pa = pyaudio.PyAudio()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
SAMPLE_SIZE = pa.get_sample_size(FORMAT)
SAMPLE_WIDTH = 2
RATE = 44100

input_stream = pa.open(format=FORMAT,
                       channels=CHANNELS,
                       rate=RATE,
                       input=True,
                       input_device_index=1,
                       frames_per_buffer=CHUNK)

output_stream = pa.open(format=pa.get_format_from_width(SAMPLE_WIDTH),
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        output_device_index=2)

# general variables
wish_id_count = 1

# sound detection parameter variables
velocity_threshold = 80
recording_minimum_length = 1
recording_length_in_seconds_of_silence_to_finish_recording = 2


def play_insult():
    directory = "C://Users/Amit/PycharmProjects/wishes-well/wishes_insults"
    # gets random file from selected directory
    file = random.choice(os.listdir(directory))
    file_to_play = "wishes_insults/" + str(file)

    wf = wave.open(file_to_play)

    data = wf.readframes(CHUNK)

    while len(data):
        output_stream.write(data)
        data = wf.readframes(CHUNK)


def listen_for_speech():
    numerator, denominator = spl.A_weighting(RATE)

    frames = []

    recording_start_timestamp = None
    speech_start_timestamp = None
    silence_start_timestamp = None

    while True:
        try:
            block = input_stream.read(CHUNK, exception_on_overflow=False)
        except IOError as e:
            print(" (%d) Error recording: %s" % e)
        else:
            # use Int16 and not anything else like Int8 or Int32
            decoded_block = numpy.frombuffer(block, numpy.int16)
            # This is where you apply A-weighted filter
            y = lfilter(numerator, denominator, decoded_block)
            new_decibel = 20 * numpy.log10(spl.rms_flat(y))
            # print(new_decibel)

            current_timestamp = time.perf_counter()

            if recording_start_timestamp is not None:
                frames.append(block)

            if new_decibel > velocity_threshold:
                # first speech - recording start
                if recording_start_timestamp is None:
                    recording_start_timestamp = time.perf_counter()

                if speech_start_timestamp is None:
                    print("speech")
                    silence_start_timestamp = None
                    speech_start_timestamp = time.perf_counter()
            else:
                if silence_start_timestamp is None and recording_start_timestamp is not None:
                    print("silence")
                    speech_start_timestamp = None
                    silence_start_timestamp = time.perf_counter()

                # checks if there's silence *AND* checks if the recording had 5 seconds of silence from last input
                if silence_start_timestamp is not None and current_timestamp - silence_start_timestamp > recording_length_in_seconds_of_silence_to_finish_recording:
                    print("recording length:", silence_start_timestamp - recording_start_timestamp)
                    #  checks if the whole recording is more than 5 minutes length
                    if silence_start_timestamp - recording_start_timestamp > recording_minimum_length:
                        play_insult()
                        return frames
                    # if recording is less than 5 seconds length it will not save it and will listen for another one
                    else:
                        print("recording isn't long enough")
                        frames = []
                        recording_start_timestamp = None
                        speech_start_timestamp = None
                        silence_start_timestamp = None


def print_input_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    num_devices = info.get('deviceCount')

    for i in range(0, num_devices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))


def generate_filename():
    global wish_id_count

    directory = "wishes_recordings/"
    filename_prefix = "wish_"
    wish_id = wish_id_count
    file_extension = ".wav"

    filename = directory + filename_prefix + str(wish_id) + file_extension

    print(filename)

    wish_id_count = wish_id_count + 1

    return filename


def write_file(frames):
    wf = wave.open(generate_filename(), 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(SAMPLE_SIZE)
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


print_input_devices()

while True:
    write_file(listen_for_speech())

input_stream.stop_stream()
input_stream.close()
pa.terminate()
