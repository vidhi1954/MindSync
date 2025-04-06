import os
import pickle
import numpy as np
import librosa
import whisper
import soundfile as sf
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_cors import CORS
import requests
from dotenv import load_dotenv
from flask_mysqldb import MySQL

# Load environment variables
load_dotenv()
GENAI_API_KEY = os.getenv("GEN_API_KEY")
if not GENAI_API_KEY:
    print("❌ API Key not found!")
else:
    print("✅ API Key loaded successfully:", GENAI_API_KEY[:5] + "****")

# Setup Flask
app = Flask(__name__)
app.secret_key = 'your-secret-key'
CORS(app, supports_credentials=True)

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'flask-users'
mysql = MySQL(app)

# Load emotion detection model
# print("🔹 Loading Speech Emotion Detection model...")
model_path = os.path.join(os.path.dirname(__file__), '..', 'SpeechEmoModel.pkl')

with open(model_path, 'rb') as f:
    emotion_model = pickle.load(f)
# print("✅ Model Loaded Successfully!")

# Routes

@app.route('/')
def home():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        pswd = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT username, password FROM tbl_users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and pswd == user[1]:
            session['username'] = user[0]
            print(f"✅ Login successful for {user[0]}")
            return redirect("http://localhost:3000")  # redirect to your React app
        else:
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        pwd = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO tbl_users (username, password) VALUES (%s, %s)", (username, pwd))
        mysql.connection.commit()
        cur.close()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/Predict', methods=['POST'])
def predict():
    try:
        print("🔹 Received a new request...")
        if "Speechfile" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["Speechfile"]
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        file_path = "temp_audio.wav"
        file.save(file_path)

        # Transcribe audio using Whisper
        print("🔹 Transcribing audio using Whisper...")
        whisper_model = whisper.load_model("base")
        result = whisper_model.transcribe(file_path)
        transcription = result["text"]
        print(f"✅ Transcription complete: {transcription}")

        # Extract MFCC and predict emotion
        features = extract_mfcc(file_path)
        prediction = emotion_model.predict(features)
        predicted_class = np.argmax(prediction)
        emotion_labels = ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Pleasant Surprised", "Sad"]
        predicted_emotion = emotion_labels[predicted_class]
        print(f"✅ Predicted Emotion: {predicted_emotion}")

        # Get Gemini response
        gemini_response = get_gemini_response(predicted_emotion, transcription)
        print(f"Gemini Response: {gemini_response}")

        return jsonify({
            "prediction_text": predicted_emotion,
            "transcript": transcription,
            "gemini_response": gemini_response
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Helper Functions

def extract_mfcc(filename):
    print(f"📢 Extracting MFCC features from {filename}...")
    y, sr = librosa.load(filename, sr=None, duration=3, offset=0.5)
    mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
    return mfcc.reshape(1, -1)

def get_gemini_response(emotion, text):
    prompt = f"""
    A person is expressing the emotion '{emotion}' and they said: "{text}".
    Provide empathetic and helpful suggestions in 100 words as bullet points for neurodiverse individuals.
    """
    print("🔹 Contacting Gemini API...")
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro-001:generateContent?key={GENAI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    response = requests.post(url, json=data, headers=headers).json()
    return response["candidates"][0]["content"]["parts"][0]["text"]

# Run app
if __name__ == '__main__':
    print("🚀 Starting MindSync Flask backend...")
    app.run(debug=True)
