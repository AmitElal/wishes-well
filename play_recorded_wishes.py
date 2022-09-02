import os
import random

from playsound import playsound


# need to implement:
# add voice changer to wishes for burners privacy

def play_insult():
    directory = "C://Users/Amit/PycharmProjects/well_of_wishes/wishes_recordings"
    # gets random file from selected directory
    file = random.choice(os.listdir(directory))
    file_to_play = "wishes_recordings/" + str(file)

    playsound(file_to_play


while True:
    play_insult()
