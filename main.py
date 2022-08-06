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

p = pyaudio.PyAudio()
info = p.get_host_api_info_by_index(0)
num_devices = info.get('deviceCount')

for i in range(0, num_devices):
    if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
        print("Input Device id ", i, " - ", p.get_device_info_by_host_api_device_index(0, i).get('name'))

stream = pa.open(format=FORMAT,
                 channels=CHANNELS,
                 rate=RATE,
                 input=True,
                 input_device_index=1,
                 frames_per_buffer=CHUNK)

velocity_threshold = 30
recording_minimum_length = 1
recording_length_in_seconds_of_silence_to_finish_recording = 5


def listen_for_speech():
    numerator, denominator = spl.A_weighting(RATE)

    frames = []

    recording_start_timestamp = None
    speech_start_timestamp = None
    silence_start_timestamp = None

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
                        return frames
                    # if recording is less than 5 seconds length it will not save it and will listen for another one
                    else:
                        print("recording isn't long enough")
                        return None


def write_file(filename, frames, channels, sample_size, frame_rate):
    wf = wave.open(filename, 'wb')
    wf.setnchannels(channels)
    wf.setsampwidth(sample_size)
    wf.setframerate(frame_rate)
    wf.writeframes(b''.join(frames))
    wf.close()


recording_frames_result = listen_for_speech()
write_file(filename="recordings/separated_voice.wav", frames=recording_frames_result, channels=1, sample_size=pa.get_sample_size(FORMAT), frame_rate=44100)

stream.stop_stream()
stream.close()
pa.terminate()
