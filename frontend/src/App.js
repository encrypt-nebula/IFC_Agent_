import React, { useState, useRef, useEffect } from "react";
import { IoSend } from "react-icons/io5";
import { FiUpload } from "react-icons/fi";
import { FaSpinner } from "react-icons/fa";
import "./index.css";

const API_BASE_URL = "http://localhost:8000";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState("");
  const [file, setFile] = useState(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState(null);
  const [apiStatus, setApiStatus] = useState("checking");
  const chatContainerRef = useRef(null);

  // Check API status on component mount
  useEffect(() => {
    const checkApiStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
          // eslint-disable-next-line no-unused-vars
          const data = await response.json();
          // Set status to "ready" even if model isn't initialized yet
          setApiStatus("ready");
        } else {
          setApiStatus("error");
        }
      } catch (error) {
        console.error("API health check failed:", error);
        setApiStatus("error");
      }
    };

    checkApiStatus();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || !file) {
      setError("Please upload an IFC file and enter a message");
      return;
    }

    const newMessage = {
      text: inputMessage,
      sender: "user",
      timestamp: new Date().toISOString(),
    };
    setMessages([...messages, newMessage]);
    setInputMessage("");
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/query`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: inputMessage,
          file_path: file.path,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to get response");
      }

      const data = await response.json();
      const botResponse = {
        text: data.response,
        sender: "bot",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, botResponse]);
    } catch (error) {
      console.error("Error:", error);
      setError(
        error.message || "Sorry, there was an error processing your request."
      );
      const errorMessage = {
        text:
          error.message || "Sorry, there was an error processing your request.",
        sender: "bot",
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith(".ifc")) {
      setIsUploading(true);
      setError(null);

      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const response = await fetch(`${API_BASE_URL}/files/upload`, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "Upload failed");
        }

        const data = await response.json();
        setFile({
          name: data.filename,
          path: data.file_path,
        });
        setUploadSuccess(true);
        setTimeout(() => setUploadSuccess(false), 3000);

        // Add a system message about the file upload
        setMessages((prev) => [
          ...prev,
          {
            text: `File "${data.filename}" uploaded successfully. You can now ask questions about this IFC file.`,
            sender: "system",
            timestamp: new Date().toISOString(),
          },
        ]);
      } catch (error) {
        console.error("Upload error:", error);
        setError(error.message || "Failed to upload file. Please try again.");
      } finally {
        setIsUploading(false);
      }
    } else {
      setError("Please upload only .ifc files");
      e.target.value = "";
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div className="app-container">
      {/* Heading */}
      <h1 className="heading">IFC Conversational AI</h1>

      {/* API Status Indicator */}
      <div className={`api-status ${apiStatus}`}>
        {apiStatus === "checking" && <FaSpinner className="spinner" />}
        {apiStatus === "ready" && <span>API Ready</span>}
        {apiStatus === "error" && <span>API Connection Error</span>}
        {apiStatus === "model-error" && <span>AI Model Error</span>}
      </div>

      {/* File Upload Section */}
      <div className="file-upload-section">
        <div className="flex items-center space-x-4">
          <label className={`upload-button ${isUploading ? "uploading" : ""}`}>
            {isUploading ? (
              <FaSpinner className="spinner" />
            ) : (
              <FiUpload className="upload-icon" />
            )}
            <span>{isUploading ? "Uploading..." : "Upload IFC File"}</span>
            <input
              type="file"
              accept=".ifc"
              onChange={handleFileUpload}
              className="hidden"
              disabled={isUploading}
            />
          </label>
          {file && (
            <span className="file-name">
              {file.name}
              {uploadSuccess && (
                <span className="upload-success">✓ Upload successful</span>
              )}
            </span>
          )}
        </div>
        {error && <div className="error-message">{error}</div>}
      </div>

      {/* Chat Container */}
      <div ref={chatContainerRef} className="chat-container">
        {messages.length === 0 && !isLoading && (
          <div className="empty-chat">
            <p>Upload an IFC file and start asking questions about it.</p>
            <p>Example questions:</p>
            <ul>
              <li>What is the total area of the building?</li>
              <li>List all the walls in the model.</li>
              <li>What materials are used in this model?</li>
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`message ${message.sender} ${
              message.isError ? "error" : ""
            }`}
          >
            <div className="message-group">
              <div className="message-header">
                <span
                  className={
                    message.sender === "bot"
                      ? "bot-label"
                      : message.sender === "system"
                      ? "system-label"
                      : "user-label"
                  }
                >
                  {message.sender === "bot"
                    ? "ChatBot:"
                    : message.sender === "system"
                    ? "System:"
                    : "You:"}
                </span>
                <span className="message-time">
                  {formatTimestamp(message.timestamp)}
                </span>
              </div>
              <div
                className={
                  message.sender === "user" ? "user-message" : "bot-message"
                }
              >
                {message.text}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message bot">
            <div className="message-group">
              <div className="message-header">
                <span className="bot-label">ChatBot:</span>
              </div>
              <div className="bot-message">
                <FaSpinner className="spinner" /> Thinking...
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSendMessage} className="input-form">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder={
            file ? "Type your message..." : "Upload an IFC file first..."
          }
          className="input-field"
          disabled={isLoading}
        />
        <button
          type="submit"
          className={`send-button ${
            !file || isLoading ? "disabled" : ""
          }`}
          disabled={isLoading || !file}
        >
          <IoSend className="send-icon" />
        </button>
      </form>
    </div>
  );
}

export default App;
