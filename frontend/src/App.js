import { useState, useRef, useEffect } from "react";

const HISTORY_KEY = "movie_chat_history";

export default function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState(() => {
    try {
      const saved = localStorage.getItem(HISTORY_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch { return []; }
  });
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(messages));
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const ask = async () => {
    if (!question.trim() || loading) return;
    const q = question;
    setMessages(prev => [...prev, { role: "user", text: q, time: new Date().toLocaleTimeString() }]);
    setQuestion("");
    setLoading(true);

    try {
      const res = await fetch("https://movie-query-app-gjzy.onrender.com/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q }),
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: "ai", text: data.answer, time: new Date().toLocaleTimeString() }]);
    } catch {
      setMessages(prev => [...prev, { role: "ai", text: "Something went wrong. Is the backend running?", time: new Date().toLocaleTimeString() }]);
    }
    setLoading(false);
  };

  const clearHistory = () => {
    if (window.confirm("Clear all chat history?")) {
      setMessages([]);
      localStorage.removeItem(HISTORY_KEY);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      backgroundColor: "#0a0a0a",
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      padding: "0 16px 32px",
      fontFamily: "'Segoe UI', sans-serif",
    }}>

      {/* Header */}
      <div style={{ textAlign: "center", padding: "36px 0 20px", width: "100%", maxWidth: 720 }}>
        <div style={{
          display: "inline-block",
          backgroundColor: "#ff1493",
          borderRadius: "50%",
          width: 52, height: 52,
          lineHeight: "52px",
          fontSize: 26,
          marginBottom: 10
        }}>🎬</div>
        <h1 style={{
          color: "#ffffff",
          fontSize: 26,
          fontWeight: 700,
          margin: "0 0 6px",
          letterSpacing: "-0.5px"
        }}>Netflix Movies and TV Shows Data Analysis</h1>
        <p style={{ color: "#ff1493", fontSize: 14, margin: "0 0 4px", fontWeight: 500 }}>
          Explore Netflix content including movies, ratings, popularity, genres.
        </p>
        <p style={{ color: "#555", fontSize: 12, margin: 0 }}>
          9,837 titles in the database
        </p>
      </div>

      {/* Chat window */}
      <div style={{
        width: "100%",
        maxWidth: 720,
        backgroundColor: "#111",
        border: "1px solid #222",
        borderRadius: 16,
        padding: "20px 16px",
        minHeight: 420,
        maxHeight: 520,
        overflowY: "auto",
        marginBottom: 16,
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}>
        {messages.length === 0 && (
          <div style={{
            flex: 1, display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center", gap: 12,
            color: "#444", fontSize: 14, textAlign: "center", padding: "60px 0"
          }}>
            <span style={{ fontSize: 36 }}>🍿</span>
            <p style={{ margin: 0 }}>Ask a question about Netflix content<br />to get started</p>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8, justifyContent: "center", marginTop: 8 }}>
              {[
                "Top 5 highest rated movies?",
                "Most popular genres?",
                "Average rating by genre?",
              ].map(s => (
                <button key={s} onClick={() => setQuestion(s)} style={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid #ff149333",
                  color: "#ff1493",
                  borderRadius: 20,
                  padding: "6px 14px",
                  fontSize: 13,
                  cursor: "pointer"
                }}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} style={{
            display: "flex",
            flexDirection: "column",
            alignItems: m.role === "user" ? "flex-end" : "flex-start",
          }}>
            <div style={{
              display: "flex",
              alignItems: "flex-end",
              gap: 8,
              flexDirection: m.role === "user" ? "row-reverse" : "row"
            }}>
              {m.role === "ai" && (
                <div style={{
                  width: 28, height: 28, borderRadius: "50%",
                  backgroundColor: "#ff1493",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, flexShrink: 0
                }}>✦</div>
              )}
              <div style={{
                backgroundColor: m.role === "user" ? "#ff1493" : "#1a1a1a",
                color: "#ffffff",
                padding: "10px 16px",
                borderRadius: m.role === "user" ? "18px 18px 4px 18px" : "18px 18px 18px 4px",
                maxWidth: "78%",
                fontSize: 14,
                lineHeight: 1.6,
                whiteSpace: "pre-wrap",
                border: m.role === "ai" ? "1px solid #222" : "none"
              }}>
                {m.text}
              </div>
            </div>
            <span style={{
              fontSize: 11, color: "#444", marginTop: 4,
              marginLeft: m.role === "ai" ? 36 : 0,
              marginRight: m.role === "user" ? 0 : 0
            }}>{m.time}</span>
          </div>
        ))}

        {loading && (
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{
              width: 28, height: 28, borderRadius: "50%",
              backgroundColor: "#ff1493",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 14
            }}>✦</div>
            <div style={{
              backgroundColor: "#1a1a1a", border: "1px solid #222",
              borderRadius: "18px 18px 18px 4px",
              padding: "10px 16px", display: "flex", gap: 4, alignItems: "center"
            }}>
              {[0, 1, 2].map(i => (
                <div key={i} style={{
                  width: 6, height: 6, borderRadius: "50%",
                  backgroundColor: "#ff1493",
                  animation: `bounce 1s ease-in-out ${i * 0.2}s infinite`
                }} />
              ))}
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div style={{
        width: "100%",
        maxWidth: 720,
        display: "flex",
        gap: 10,
        backgroundColor: "#111",
        border: "1px solid #ff149355",
        borderRadius: 14,
        padding: "8px 8px 8px 16px",
        alignItems: "center",
        boxShadow: "0 0 20px #ff149315"
      }}>
        <input
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => e.key === "Enter" && ask()}
          placeholder="Ask about Netflix movies, genres, ratings..."
          style={{
            flex: 1,
            backgroundColor: "transparent",
            border: "none",
            outline: "none",
            color: "#ffffff",
            fontSize: 15,
            caretColor: "#ff1493",
          }}
        />
        <button
          onClick={ask}
          disabled={loading}
          style={{
            backgroundColor: loading ? "#333" : "#ff1493",
            color: "#fff",
            border: "none",
            borderRadius: 10,
            padding: "10px 20px",
            fontSize: 14,
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer",
            transition: "background 0.2s",
            whiteSpace: "nowrap"
          }}
        >
          {loading ? "Thinking..." : "Ask ✦"}
        </button>
      </div>

      {/* Footer */}
      <div style={{ display: "flex", gap: 16, alignItems: "center", marginTop: 12 }}>
        <p style={{ color: "#333", fontSize: 12, margin: 0 }}>
          Powered by Gemini · SQLite · FastAPI
        </p>
        {messages.length > 0 && (
          <button onClick={clearHistory} style={{
            backgroundColor: "transparent",
            border: "1px solid #333",
            color: "#555",
            borderRadius: 6,
            padding: "3px 10px",
            fontSize: 12,
            cursor: "pointer"
          }}>Clear history</button>
        )}
      </div>

      <style>{`
        @keyframes bounce {
          0%, 100% { transform: translateY(0); opacity: 0.4; }
          50% { transform: translateY(-4px); opacity: 1; }
        }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #111; }
        ::-webkit-scrollbar-thumb { background: #ff149355; border-radius: 4px; }
        * { box-sizing: border-box; }
      `}</style>
    </div>
  );
}