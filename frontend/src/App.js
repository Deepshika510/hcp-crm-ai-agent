import { useState, useEffect } from "react";
import axios from "axios";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [mode, setMode] = useState("form"); // "form" or "chat"

  const [formData, setFormData] = useState({
    hcp_id: "",
    channel: "in-person",
    products_discussed: "",
    summary: "",
    sentiment: "positive",
    follow_up_action: "",
    raw_input: "",
  });

  const [interactions, setInteractions] = useState([]);

  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  const fetchInteractions = async () => {
    const res = await axios.get(`${API_URL}/interactions`);
    setInteractions(res.data);
  };

  useEffect(() => {
    fetchInteractions();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post(`${API_URL}/interactions`, {
      ...formData,
      hcp_id: parseInt(formData.hcp_id),
    });
    setFormData({
      hcp_id: "",
      channel: "in-person",
      products_discussed: "",
      summary: "",
      sentiment: "positive",
      follow_up_action: "",
      raw_input: "",
    });
    fetchInteractions();
  };

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatMessages((prev) => [...prev, { role: "user", text: userMessage }]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await axios.post(`${API_URL}/chat`, { message: userMessage });
      setChatMessages((prev) => [
        ...prev,
        { role: "agent", text: res.data.reply, intent: res.data.intent },
      ]);
      fetchInteractions();
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "agent", text: "Sorry, something went wrong." },
      ]);
    }

    setChatLoading(false);
  };

  const handleChatKeyDown = (e) => {
    if (e.key === "Enter") {
      handleChatSend();
    }
  };

  return (
    <div style={{ padding: "40px", fontFamily: "Inter, sans-serif", maxWidth: "700px" }}>
      <h1>HCP Log Interaction</h1>

      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={() => setMode("form")}
          style={{
            padding: "8px 16px",
            marginRight: "10px",
            fontWeight: mode === "form" ? "bold" : "normal",
            backgroundColor: mode === "form" ? "#4CAF50" : "#eee",
            color: mode === "form" ? "white" : "black",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          📝 Structured Form
        </button>
        <button
          onClick={() => setMode("chat")}
          style={{
            padding: "8px 16px",
            fontWeight: mode === "chat" ? "bold" : "normal",
            backgroundColor: mode === "chat" ? "#4CAF50" : "#eee",
            color: mode === "chat" ? "white" : "black",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          💬 Chat Assistant
        </button>
      </div>

      {mode === "form" && (
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: "10px" }}>
            <label>HCP ID: </label>
            <input type="number" name="hcp_id" value={formData.hcp_id} onChange={handleChange} required />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label>Channel: </label>
            <select name="channel" value={formData.channel} onChange={handleChange}>
              <option value="in-person">In-person</option>
              <option value="virtual">Virtual</option>
              <option value="phone">Phone</option>
            </select>
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label>Products Discussed: </label>
            <input type="text" name="products_discussed" value={formData.products_discussed} onChange={handleChange} />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label>Summary: </label>
            <textarea name="summary" value={formData.summary} onChange={handleChange} />
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label>Sentiment: </label>
            <select name="sentiment" value={formData.sentiment} onChange={handleChange}>
              <option value="positive">Positive</option>
              <option value="neutral">Neutral</option>
              <option value="negative">Negative</option>
            </select>
          </div>

          <div style={{ marginBottom: "10px" }}>
            <label>Follow-up Action: </label>
            <input type="text" name="follow_up_action" value={formData.follow_up_action} onChange={handleChange} />
          </div>

          <button type="submit">Save Interaction</button>
        </form>
      )}

      {mode === "chat" && (
        <div>
          <div
            style={{
              border: "1px solid #ccc",
              borderRadius: "8px",
              padding: "10px",
              height: "300px",
              overflowY: "auto",
              marginBottom: "10px",
              backgroundColor: "#fafafa",
            }}
          >
            {chatMessages.length === 0 && (
              <p style={{ color: "#888" }}>
                Try: "Met Dr Sharma today, discussed CardioX, she's interested" or "Show me history for HCP 1"
              </p>
            )}
            {chatMessages.map((msg, idx) => (
              <div
                key={idx}
                style={{
                  textAlign: msg.role === "user" ? "right" : "left",
                  marginBottom: "8px",
                }}
              >
                <span
                  style={{
                    display: "inline-block",
                    padding: "8px 12px",
                    borderRadius: "12px",
                    backgroundColor: msg.role === "user" ? "#4CAF50" : "#e0e0e0",
                    color: msg.role === "user" ? "white" : "black",
                    maxWidth: "80%",
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {msg.text}
                </span>
              </div>
            ))}
            {chatLoading && <p style={{ color: "#888" }}>Agent is thinking...</p>}
          </div>

          <div style={{ display: "flex" }}>
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={handleChatKeyDown}
              placeholder="Type your message..."
              style={{ flex: 1, padding: "8px", marginRight: "8px" }}
            />
            <button onClick={handleChatSend}>Send</button>
          </div>
        </div>
      )}

      <h2 style={{ marginTop: "40px" }}>Logged Interactions</h2>
      <ul>
        {interactions.map((i) => (
          <li key={i.id}>
            #{i.id} — HCP #{i.hcp_id} — {i.channel} — {i.products_discussed} — {i.sentiment}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;