import { useState } from "react";
import axios from "axios";

export default function App() {
  const [file, setFile] = useState(null);
  const [selectedFileName, setSelectedFileName] = useState("");
  const [uploadResult, setUploadResult] = useState("");
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState("");
  const [uploading, setUploading] = useState(false);
  const [thinking, setThinking] = useState(false);

  const API_BASE = "https://chatbot-service-874596362722.northamerica-northeast1.run.app";

  async function uploadFile() {
    if (!file) {
      alert("Please select a file first");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      setUploading(true);
      setUploadResult("");

      const res = await axios.post(`${API_BASE}/ingest`, formData);

      setUploadResult(
        res.data?.stats?.message ||
          res.data?.message ||
          "Document uploaded successfully."
      );
    } catch (err) {
      console.error("UPLOAD ERROR:", err);

      setUploadResult(
        err.response?.data?.detail ||
          err.message ||
          "Upload failed"
      );
    } finally {
      setUploading(false);
    }
  }

  async function askQuestion() {
    if (!question) return;

    try {
      setThinking(true);
      setResponse("");

      const res = await axios.post(`${API_BASE}/chat`, {
        message: question,
      });

      console.log("CHAT RESPONSE:", res.data);

      setResponse(
        res.data?.response ||
          res.data?.answer ||
          res.data?.message ||
          JSON.stringify(res.data, null, 2)
      );
    } catch (err) {
      console.error("CHAT ERROR:", err);

      setResponse(
        err.response?.data?.detail ||
          err.message ||
          "Request failed"
      );
    } finally {
      setThinking(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background:
          "linear-gradient(to bottom right, #0f172a, #111827, #1e293b)",
        color: "white",
        padding: "40px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "950px",
          margin: "0 auto",
        }}
      >
        {/* Header */}
        <div
          style={{
            textAlign: "center",
            marginBottom: "40px",
          }}
        >
          <h1
            style={{
              fontSize: "48px",
              marginBottom: "10px",
            }}
          >
            RAG Chatbot
          </h1>

          <p
            style={{
              color: "#cbd5e1",
              fontSize: "18px",
            }}
          >
            Upload documents and chat with your knowledge base
          </p>
        </div>

        {/* Upload Section */}
        <div
          style={{
            background: "#1e293b",
            padding: "30px",
            borderRadius: "20px",
            marginBottom: "30px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>
            Upload Document
          </h2>

          <input
            type="file"
            onChange={(e) => {
              const selected = e.target.files[0];

              setFile(selected);
              setSelectedFileName(selected?.name || "");

              // allows re-uploading same file
              e.target.value = null;
            }}
            style={{
              marginBottom: "15px",
              color: "white",
            }}
          />

          {selectedFileName && (
            <div
              style={{
                marginBottom: "20px",
                color: "#94a3b8",
              }}
            >
              Selected: <strong>{selectedFileName}</strong>
            </div>
          )}

          <button
            onClick={uploadFile}
            disabled={uploading}
            style={{
              background: uploading
                ? "#475569"
                : "linear-gradient(to right, #3b82f6, #2563eb)",
              color: "white",
              border: "none",
              padding: "12px 22px",
              borderRadius: "10px",
              fontSize: "16px",
              fontWeight: "bold",
              cursor: "pointer",
            }}
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>

          {uploadResult && (
            <div
              style={{
                marginTop: "20px",
                background: "#0f172a",
                padding: "16px",
                borderRadius: "10px",
                color: "#e2e8f0",
                border: "1px solid #334155",
              }}
            >
              {uploadResult}
            </div>
          )}
        </div>

        {/* Chat Section */}
        <div
          style={{
            background: "#1e293b",
            padding: "30px",
            borderRadius: "20px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.3)",
          }}
        >
          <h2 style={{ marginBottom: "20px" }}>
            Ask Questions
          </h2>

          <div
            style={{
              display: "flex",
              gap: "12px",
            }}
          >
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask something about your documents..."
              style={{
                flex: 1,
                padding: "14px",
                borderRadius: "10px",
                border: "1px solid #334155",
                background: "#0f172a",
                color: "white",
                fontSize: "16px",
                outline: "none",
              }}
            />

            <button
              onClick={askQuestion}
              disabled={thinking}
              style={{
                background: thinking
                  ? "#475569"
                  : "linear-gradient(to right, #22c55e, #16a34a)",
                color: "white",
                border: "none",
                padding: "14px 24px",
                borderRadius: "10px",
                fontSize: "16px",
                fontWeight: "bold",
                cursor: "pointer",
              }}
            >
              {thinking ? "Thinking..." : "Ask"}
            </button>
          </div>

          {response && (
            <div
              style={{
                marginTop: "25px",
                background: "#0f172a",
                padding: "24px",
                borderRadius: "12px",
                border: "1px solid #334155",
                lineHeight: "1.8",
                color: "#f1f5f9",
                whiteSpace: "pre-wrap",
                fontSize: "16px",
              }}
            >
              {response}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}