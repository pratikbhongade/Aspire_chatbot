import sounddevice as sd
import queue
import vosk
import json

# Load the VOSK model
model_path = "model/vosk-model-small-en-us-0.15"  # Adjust the path to your VOSK model
vosk_model = vosk.Model(model_path)

# Queue for storing audio data
q = queue.Queue()

def callback(indata, frames, time, status):
    """Callback function for capturing audio data."""
    if status:
        print(status)
    q.put(bytes(indata))

def recognize_speech():
    """Capture audio and recognize speech using VOSK."""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("Listening...")
        rec = vosk.KaldiRecognizer(vosk_model, 16000)
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                result_dict = json.loads(result)
                if result_dict.get("text"):
                    print("You said:", result_dict["text"])
                    return result_dict["text"]
