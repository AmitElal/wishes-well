import pyaudio
from scipy.signal import lfilter
import spl_lib as spl
import numpy
import wave
import time


pa = pyaudio.PyAudio()

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

info = pa.get_host_api_info_by_index(0)

stream = pa.open(format=FORMAT,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 input_device_index=1,
                 frames_per_buffer=CHUNK)


def get_recording_frames():
    numerator, denominator = spl.A_weighting(RATE)
    all_frames = []
    selected_frames = []

    while_start_timestamp = time.perf_counter()
    while True:
        try:
            block = stream.read(CHUNK, exception_on_overflow=False)
        except IOError as e:
            print(" (%d) Error recording: %s" % e)
        else:
            # use Int16 and not anything else like Int8 or Int32
            decoded_block = numpy.frombuffer(block, numpy.int16)
            # This is where you apply A-weighted filter
            y = lfilter(numerator, denominator, decoded_block)
            new_decibel = 20 * numpy.log10(spl.rms_flat(y))
            print(new_decibel)

            all_frames.append(block)
            if new_decibel > 38:
                selected_frames.append(block)

            if time.perf_counter() - while_start_timestamp > 10:
                break
    return [all_frames, selected_frames]


def write_file(filename, frames, channels, sample_size, frame_rate):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sample_size)
    wf.setframerate(frame_rate)
    wf.writeframes(b''.join(frames))
    wf.close()


all_frames, selected_frames = get_recording_frames()

write_file(filename="recordings/all_frames.wav", frames=all_frames, channels=1, sample_size=pa.get_sample_size(FORMAT), frame_rate=44100)
write_file(filename="recordings/selected_frames.wav", frames=selected_frames, channels=1, sample_size=pa.get_sample_size(FORMAT), frame_rate=44100)

stream.stop_stream()
stream.close()
pa.terminate()
