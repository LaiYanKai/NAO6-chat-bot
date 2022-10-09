from naoqi import ALProxy
import vision_definitions
import subprocess
# import speech_recognition as sr
import time
import sys
from os import path

fpath = path.dirname(path.realpath(__file__))
AUDIO_FILE = path.join(fpath, "test.wav")
mem = ALProxy("ALMemory", "nao.local", 9559)
tts = ALProxy("ALTextToSpeech", "nao.local", 9559)
tts.say("Ready")

aud = ALProxy("ALAudioRecorder", "nao.local", 9559)
aud.stopMicrophonesRecording()
# time.sleep(5)
# aud.stopMicrophonesRecording()

# obtain path to "english.wav" in the same folder as this script
# r = sr.Recognizer()
#with sr.AudioFile(AUDIO_FILE) as source:
#    audio = r.record(source)  # read the entire audio file

#try:
    # for testing purposes, we're just using the default API key
    # to use another API key, use `r.recognize_google(audio, key="GOOGLE_SPEECH_RECOGNITION_API_KEY")`
    # instead of `r.recognize_google(audio)`
#    print("Google Speech Recognition thinks you said " + r.recognize_google(audio))
#except sr.UnknownValueError:
#    print("Google Speech Recognition could not understand audio")
#except sr.RequestError as e:
#    print("Could not request results from Google Speech Recognition service; {0}".format(e))

asr = ALProxy("ALSpeechRecognition", "nao.local", 9559)
asr.setLanguage("English")
# Example: Adds "yes", "no" and "please" to the vocabulary (without wordspotting)
asr.pause(True)
vocabulary = ["Are", "Is", 
"born", "work", "Greetings", "I", 
"Nao", 
"Hello", "Hey", "Hi", "Good", "How", "Who", "What", 
"Where", "Tell", "a"]
asr.setVocabulary(vocabulary, True)
asr.pause(False)
f = open("hs.txt", "w")
f.write("0")
f.close()
f = open("pc.txt", "w")
f.write("0")
f.close()

# Start the speech recognition engine with user Test_ASR
seq = 1
pc_seq = 0
asr.subscribe("Test_ASR")
print("Ready")

raw_input("Press Enter to continue...")

aud.startMicrophonesRecording(AUDIO_FILE, "wav", 16000, [0,0,1,0])

invalid_responses = [
  "Sorry, could you repeat that?",
  "Can you say that again?",
  "I didn't catch that",
  "Sorry, I didn't catch that",
  "Please say that again?",
  "Sorry, I can't hear you"
]
ir = 0
while True:
  if mem.getData("SpeechDetected"):
    asr.pause(True)
    print("Speech Detected: " + repr(mem.getData("WordRecognized")))
    try:
      time.sleep(2)
    except KeyboardInterrupt:
      aud.stopMicrophonesRecording()
      sys.exit()

    aud.stopMicrophonesRecording()
    asr.pause(False)
    print("Stop Recording")
    f = open("hs.txt", "w")
    f.write(str(seq))
    seq += 1
    f.close()

    while True:
      try:
        s = str(subprocess.check_output(['cat', 'pc.txt']))
        if s and int(s) != pc_seq:
          pc_seq = int(s)
          response = str(subprocess.check_output(['cat', 'response.txt']))
          if not response:
            response = invalid_responses[ir]
            ir += 1
            if ir >=len(invalid_responses):
              ir = 0
          
          print("Responding: " + response)
          tts.say(response)
          f.close()
          break
      except KeyboardInterrupt:
        sys.exit()
    aud.startMicrophonesRecording(AUDIO_FILE, "wav", 16000, [0,0,1,0])

  
asr.unsubscribe("Test_ASR")
