import argparse
from tkinter import dialog
import paramiko
import time
import os
import sys
from google.cloud import dialogflow

LOCAL_DIR_SCRIPT = os.path.dirname(os.path.realpath(__file__))
# NAO_TRANSCRIBED_FILE = "/home/nao/robot/test.txt"
# LOCAL_TRANSCRIBED_FILE = os.path.join(LOCAL_DIR_SCRIPT, "test.txt")
NAO_HANDSHAKE_FILE = "/home/nao/robot/hs.txt"
NAO_AUDIO_FILE = "/home/nao/robot/test.wav"
LOCAL_AUDIO_FILE = os.path.join(LOCAL_DIR_SCRIPT, "test.wav")
LOCAL_PCHS_FILE = os.path.join(LOCAL_DIR_SCRIPT, "pc.txt")
NAO_PCHS_FILE = "/home/nao/robot/pc.txt"
LOCAL_RESPONSE_FILE = os.path.join(LOCAL_DIR_SCRIPT, "response.txt")
NAO_RESPONSE_FILE = "/home/nao/robot/response.txt"

NAO_IP = '192.168.10.100'
NAO_USER = 'nao'
NAO_PASS = 'nao'

SESSION_ID = "4"
PROJECT_ID = "small-talk-ptky"
session_client = dialogflow.SessionsClient()
session = session_client.session_path(PROJECT_ID, SESSION_ID)
print("Session path: {}\n".format(session))
print(dialogflow.AgentsClient().agent_path(PROJECT_ID))

def detect_intent_audio(audio_file_path, language_code):
    """Returns the result of detect intent with an audio file as input.
    Using the same `session_id` between requests allows continuation
    of the conversation."""

    # Note: hard coding audio_encoding and sample_rate_hertz for simplicity.
    audio_encoding = dialogflow.AudioEncoding.AUDIO_ENCODING_LINEAR_16
    sample_rate_hertz = 16000

    if os.path.getsize(audio_file_path) > 1000000:
        print("WAV file exceeded 1000KB (" + str(os.path.getsize(audio_file_path)) + " KB)")
        return ""

    with open(audio_file_path, "rb") as audio_file:
        input_audio = audio_file.read()
        

    if not input_audio:
        return ""

    audio_config = dialogflow.InputAudioConfig(
        audio_encoding=audio_encoding,
        language_code=language_code,
        sample_rate_hertz=sample_rate_hertz,
    )
    query_input = dialogflow.QueryInput(audio_config=audio_config)

    request = dialogflow.DetectIntentRequest(
        session=session, query_input=query_input, input_audio=input_audio,
    )
    response = session_client.detect_intent(request=request)

    print("Query text: {}".format(response.query_result.query_text))
    print(
        "Detected intent: {} (confidence: {})\n".format(
            response.query_result.intent.display_name,
            response.query_result.intent_detection_confidence,
        )
    )
    print("Fulfillment text: {}\n".format(
        response.query_result.fulfillment_text))
    return response.query_result.fulfillment_text


def detect_intent_texts(texts, language_code):
    """Returns the result of detect intent with texts as inputs.

    Using the same `session_id` between requests allows continuation
    of the conversation."""

    responses = []

    for text in texts:
        text_input = dialogflow.TextInput(
            text=text, language_code=language_code)

        query_input = dialogflow.QueryInput(text=text_input)

        response = session_client.detect_intent(
            request={"session": session, "query_input": query_input}
        )

        print("Query text: {}".format(response.query_result.query_text))
        print(
            "Detected intent: {} (confidence: {})\n".format(
                response.query_result.intent.display_name,
                response.query_result.intent_detection_confidence,
            )
        )
        print("Fulfillment text: {}\n".format(
            response.query_result.fulfillment_text))
        responses.append(response.query_result.fulfillment_text)
    return responses


# detect_intent_texts(["who are you","how are you", "where do you work", "give me a hug", "how old are you"], "en")
# sys.exit()


ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname=NAO_IP, username=NAO_USER, password=NAO_PASS)
ftp_client = ssh_client.open_sftp()

stdin, stdout, stderr = ssh_client.exec_command("cat " + NAO_HANDSHAKE_FILE)
prev_seq = int(stdout.readline())
pc_seq = 1

while True:

    # get modified time
    stdin, stdout, stderr = ssh_client.exec_command(
        "cat " + NAO_HANDSHAKE_FILE)
    try:
        seq = int(stdout.readline())
    except:
        pass
    # print(prev_seq, seq)

    if prev_seq != seq:
        print("=" * 20)
        print("Query Detected: {}".format(seq))
        prev_seq = seq
        ftp_client.get(NAO_AUDIO_FILE, LOCAL_AUDIO_FILE)

        # f = open(LOCAL_TRANSCRIBED_FILE)
        # text = f.readline()
        # print([sec_last_mod, text])
        # detect_intent_texts(PROJECT_ID, SESSION_ID, [text], "English")

        response = detect_intent_audio(LOCAL_AUDIO_FILE, "en")

        f = open(LOCAL_RESPONSE_FILE, "w")
        f.write(response)
        f.close()
        ftp_client.put(LOCAL_RESPONSE_FILE, NAO_RESPONSE_FILE)

        f = open(LOCAL_PCHS_FILE, "w")
        f.write(str(pc_seq))
        pc_seq += 1
        f.close()
        ftp_client.put(LOCAL_PCHS_FILE, NAO_PCHS_FILE)

        # f.close()

    time.sleep(0.1)

ftp_client.close()
