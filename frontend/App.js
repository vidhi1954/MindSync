import React, { useState, useEffect } from "react";
import axios from "axios";
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/icon?family=Material+Icons"
/>
function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [prediction, setPrediction] = useState("");
  const [transcription, setTranscription] = useState("");
  const [geminiResponse, setGeminiResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState("home");
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [audioChunks, setAudioChunks] = useState([]);

  const [bgColor, setBgColor] = useState("#e0f7fa");

  useEffect(() => {
    if (page === "home") {
      const colors = ["#e0f7fa", "#ffebee", "#c8e6c9", "#fff3e0"];
      let index = 0;
      const interval = setInterval(() => {
        setBgColor(colors[index]);
        index = (index + 1) % colors.length;
      }, 5000);

      return () => clearInterval(interval);
    }
  }, [page]);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      alert("Please select a file first!");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("Speechfile", selectedFile);

    try {
      const response = await axios.post("http://127.0.0.1:5000/Predict", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      setPrediction(response.data.prediction_text || "No prediction available");
      setTranscription(response.data.transcript || "No transcript available");
      setGeminiResponse(response.data.gemini_response || "No Gemini response available");
    } catch (error) {
      setPrediction("Error occurred");
      setTranscription("Error occurred");
      setGeminiResponse("Error occurred");
    }

    setLoading(false);
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);

      setMediaRecorder(recorder);
      setAudioChunks([]);

      let tempChunks = [];
      recorder.ondataavailable = (event) => {
        tempChunks.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(tempChunks, { type: "audio/mp4" });
        setAudioChunks(tempChunks);

        const formData = new FormData();
        formData.append("Speechfile", audioBlob, "temp.mp4");

        setLoading(true);
        try {
          const response = await axios.post("http://127.0.0.1:5000/Predict", formData, {
            headers: { "Content-Type": "multipart/form-data" },
          });

          setPrediction(response.data.prediction_text || "No prediction available");
          setTranscription(response.data.transcript || "No transcript available");
          setGeminiResponse(response.data.gemini_response || "No Gemini response available");
        } catch (error) {
          setPrediction("Error occurred");
          setTranscription("Error occurred");
          setGeminiResponse("Error occurred");
        }
        setLoading(false);
      };

      recorder.start();
      setRecording(true);

      setTimeout(() => {
        recorder.stop();
        setRecording(false);
      }, 5000);
    } catch (error) {
      console.error("Error starting recording:", error);
    }
    setPage("record");
  };

  return (
    <div style={{ ...styles.container, backgroundColor: bgColor }}>
      {page === "home" ? (
        <div style={styles.home}>
          <h1 style={styles.title}>MindSync</h1>
          <p style={styles.subtitle}>A calm, interactive space to understand your emotions better</p>
          <div style={styles.descriptionContainer}>
            <p style={styles.descriptionText}>
              MindSync uses AI to help you identify and understand your emotions by analyzing your voice.
              Whether you're feeling stressed, joyful, or anywhere in between, we provide insights to help you
              navigate your emotional landscape with ease. Simply upload or record your voice, and let us analyze it.
            </p>
          </div>
          <div style={styles.scrollButtonsContainer}>
            <button style={styles.button} onClick={() => setPage("upload")}>
              <i className="fas fa-upload" style={styles.icon}></i> Upload Audio File
            </button>
            <button style={styles.button} onClick={startRecording} disabled={recording}>
              <i className="fas fa-microphone" style={styles.icon}></i>
              {recording ? " Recording..." : " Use Microphone"}
            </button>
          </div>
        </div>
      ) : (
        <div style={styles.analysis}>
          <h1 style={styles.title}>Emotion Detection</h1>

          {page === "upload" && (
            <>
              <input type="file" onChange={handleFileChange} style={styles.input} />
              <button style={styles.button} onClick={handleUpload} disabled={loading}>
                {loading ? "Processing..." : <><i className="fas fa-upload" style={styles.icon}></i> Upload & Analyze</>}
              </button>
            </>
          )}

          {page === "record" && (
            <>
              <button style={styles.button} onClick={startRecording} disabled={recording}>
                {recording ? "Recording..." : "Record Again"}
              </button>
            </>
          )}

          <div style={styles.resultContainer}>
            <h2 style={styles.text}>Prediction:</h2>
            <p style={styles.predictionText}>{prediction}</p>
            <h2 style={styles.text}>Transcript:</h2>
            <p style={styles.predictionText}>{transcription}</p>

            <h2 style={styles.text}>Gemini Response:</h2>
            <div style={styles.responseContainer}>
              <ul>
                {geminiResponse
                  ? geminiResponse.split("* **").map((item, index) =>
                      item.trim() ? <li key={index}>{item.trim()}</li> : null
                    )
                  : <li>Waiting for response...</li>}
              </ul>
            </div>
          </div>

          <button style={styles.button} onClick={() => setPage("home")}>
            Back to Home
          </button>
        </div>
      )}
    </div>
  );
}

const styles = {
  container: {
    textAlign: "center",
    fontFamily: "'Arial', sans-serif",
    minHeight: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    flexDirection: "column",
    padding: "0 20px",
    transition: "background-color 0.5s ease", 
    overflowY: "auto",
  },
  home: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    marginTop: "20px",
  },
  title: {
    fontSize: "3rem",
    fontWeight: "bold",
    color: "#5e5e5e",
    marginBottom: "30px",
    fontFamily: "'Lobster', cursive",
    textAlign: "center",
  },
  subtitle: {
    fontSize: "1.25rem",
    color: "#7a7a7a",
    marginBottom: "30px",
  },
  descriptionContainer: {
    maxWidth: "600px",
    marginBottom: "40px",
  },
  descriptionText: {
    fontSize: "1rem",
    color: "#555",
    textAlign: "center",
    lineHeight: "1.5",
  },
  scrollButtonsContainer: {
    display: "flex",
    flexDirection: "column", 
    gap: "20px", 
    alignItems: "center", 
  },
  button: {
    backgroundColor: "#5f8c8f",
    color: "white",
    padding: "14px 30px",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
    transition: "all 0.3s ease",
    width: "200px", 
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
  },
  icon: {
    marginRight: "10px", 
  },
  input: {
    padding: "10px",
    fontSize: "16px",
    borderRadius: "5px",
    border: "1px solid #ccc",
    marginBottom: "15px",
    width: "60%",
  },
  text: {
    fontSize: "1.5rem",
    fontWeight: "bold",
    color: "#333",
  },
  resultContainer: {
    marginTop: "30px",
    backgroundColor: "#ffffff",
    padding: "20px",
    borderRadius: "10px",
    boxShadow: "0 4px 10px rgba(0, 0, 0, 0.1)",
    textAlign: "left",
    maxWidth: "800px",
    margin: "0 auto",
  },
  predictionText: {
    fontSize: "1rem",
    color: "#555",
  },
  responseContainer: {
    textAlign: "left",
    padding: "10px 0",
  },
};

export default App;