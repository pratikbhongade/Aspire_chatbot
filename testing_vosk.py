import sounddevice as sd
import queue
import vosk
import json

# Load VOSK model
model_path = "model/vosk-model-small-en-us-0.15"  # Adjust to the path where your model is stored
model = vosk.Model(model_path)

# Initialize a queue to store audio data
q = queue.Queue()

def callback(indata, frames, time, status):
    """This is called for each audio block from the microphone."""
    if status:
        print(status)
    q.put(bytes(indata))

def recognize_speech():
    """Capture audio from microphone and recognize speech using VOSK."""
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        print("Listening... Please speak into the microphone.")
        recognizer = vosk.KaldiRecognizer(model, 16000)
        while True:
            data = q.get()
            if recognizer.AcceptWaveform(data):
                result = recognizer.Result()
                result_dict = json.loads(result)
                if result_dict.get("text"):
                    print("You said:", result_dict["text"])
                    return result_dict["text"]

if __name__ == "__main__":
    try:
        recognized_text = recognize_speech()
        if recognized_text:
            print(f"Recognized text: {recognized_text}")
        else:
            print("No speech detected.")
    except Exception as e:
        print(f"Error occurred: {e}")
