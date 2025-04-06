import os
import pickle
import numpy as np
import librosa
import whisper
import soundfile as sf
import google.generativeai as genai
from flask import Flask, request, jsonify
from flask_cors import CORS  
import requests
from dotenv import load_dotenv  

# Load environment variables
load_dotenv()
GENAI_API_KEY = os.getenv("GEN_API_KEY")
if not GENAI_API_KEY:
    print("❌ API Key not found!")
else:
    print("✅ API Key loaded successfully:", GENAI_API_KEY[:5] + "****")

# Configure Google Gemini API
genai.configure(api_key=GENAI_API_KEY)
import google.generativeai as genai

flask_app = Flask(__name__)
CORS(flask_app)  

# Load speech emotion model
print("🔹 Loading Speech Emotion Detection model...")
model_path = os.path.join(os.path.dirname(__file__), '..', 'SpeechEmoModel.pkl')

with open(model_path, 'rb') as f:
    emotion_model = pickle.load(f)
print("✅ Model Loaded Successfully!")

def extract_mfcc(filename):
    """Extracts MFCC features from an audio file."""
    print(f"📢 Extracting MFCC features from {filename}...")
    y, sr = librosa.load(filename, sr=None, duration=3, offset=0.5)
    mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
    print("✅ MFCC extraction complete!")
    return mfcc.reshape(1, -1)  # Reshape for model input

def get_gemini_response(emotion, text):
    
    prompt = f"""
    A person is expressing the emotion '{emotion}' and they said: "{text}". 
    How should someone respond to them? Provide empathetic and helpful suggestions.
    """
    print("🔹 Contacting Gemini AI for response...")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-001:generateContent?key={GENAI_API_KEY}"

    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": f"""Suggest some answers to a neuroDiverse individual to a
    A person who is expressing the emotion '{emotion}' and they said: "{text}". 
    Provide empathetic and helpful suggestions.Give answer in bullets , 100 words
    """}]}]}

    response = requests.post(url, json=data, headers=headers).json()
    print("generating response")
    return f"Response: {response['candidates'][0]['content']['parts'][0]['text']}"


    # try:
    #     model = genai.GenerativeModel("gemini-pro")
    #     response = model.generate_content(prompt)
    #     print("✅ Gemini AI response received!")
    #     return response.text.strip() if response else "No response generated."
    # except Exception as e:
    #     print(f"❌ Error with Gemini API: {str(e)}")
    #     return f"Error with Gemini API: {str(e)}"

@flask_app.route("/")
def home():
    return jsonify({"message": "Welcome to Speech Emotion Detection API"})

@flask_app.route("/Predict", methods=["POST"])
def predict():
    try:
        print("🔹 Received a new request...")
        print("Request content-type:", request.content_type)  
        print("Request files:", request.files)  

        if "Speechfile" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["Speechfile"]
        print("📢 Uploaded filename:", file.filename)  

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        file_path = "temp_audio.wav"
        file.save(file_path)

        print("🎤 Processing audio file...")  

        # Transcription using Whisper
        print("🔹 Transcribing audio using Whisper...")
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(file_path)
        transcription = result["text"]
        print(f"✅ Transcription complete: {transcription}")

        # Extract MFCC features
        features = extract_mfcc(file_path)

        # Predict emotion
        print("🔹 Predicting emotion from speech...")
        prediction = emotion_model.predict(features)  
        predicted_class = np.argmax(prediction)

        # Emotion labels
        emotion_labels = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Pleasant Surprised", "Sad"]
        predicted_emotion = emotion_labels[predicted_class]  
        print(f"✅ Predicted Emotion: {predicted_emotion}")

        # Get response from Gemini AI
        gemini_response = get_gemini_response(predicted_emotion, transcription)
        print(f"Response:{gemini_response}")

        return jsonify({
            "prediction_text": predicted_emotion,
            "transcript": transcription,
            "gemini_response": gemini_response
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("🚀 Starting Flask app...")
    flask_app.run(debug=True)
