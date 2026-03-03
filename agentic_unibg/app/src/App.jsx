import { useState, useEffect, useRef } from "react";
import "./App.css";
import LoginPage from "./LoginPage";
import SettingsPage from "./SettingsPage";
import unibgLogo from "./img/unibg_logo.png";

function App() {
  const [message, setMessage] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loading, setLoading] = useState(false);
  const conversationEndRef = useRef(null);
  const [connectionStatus, setConnectionStatus] = useState("checking");
  const [showWorkflow, setShowWorkflow] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Auth state
  const [userInfo, setUserInfo] = useState(null); // null = not logged in, show login page
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isInitialLoading, setIsInitialLoading] = useState(true);

  useEffect(() => {
    // Test connection to backend
    fetch("/api/health")
      .then((res) => res.json())
      .then((data) => {
        console.log("Backend status:", data);
        setConnectionStatus("connected");
      })
      .catch((err) => {
        console.error("Backend connection error:", err);
        setConnectionStatus("error");
      });

    // Verifica token dal cookie
    fetch("/api/auth/verify", {
      credentials: "include",
    })
      .then((res) => {
        if (!res.ok) throw new Error("Token invalido");
        return res.json();
      })
      .then((userData) => {
        setUserInfo(userData);
        setIsAuthenticated(true);
        const key = `conversation_${userData.matricola || "ospite"}`;
        const saved = localStorage.getItem(key);
        if (saved) {
          try {
            setConversation(JSON.parse(saved));
          } catch (e) {}
        }
      })
      .catch((err) => {
        console.error("Token verification failed:", err);
      })
      .finally(() => {
        setIsInitialLoading(false);
      });
  }, []);

  // Auto-scroll al fondo quando arriva un nuovo messaggio
  useEffect(() => {
    conversationEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation, loading]);

  // Salva conversazione in localStorage ad ogni aggiornamento
  useEffect(() => {
    if (isAuthenticated && userInfo) {
      const key = `conversation_${userInfo.matricola || "ospite"}`;
      localStorage.setItem(key, JSON.stringify(conversation));
    }
  }, [conversation, isAuthenticated, userInfo]);

  // Auth handlers
  const handleLogin = (userData) => {
    setUserInfo(userData);
    setIsAuthenticated(true);
    // Il login è riuscito → il server è raggiungibile
    setConnectionStatus("connected");
  };

  const handleGuest = () => {
    setUserInfo({
      status: "ospite",
      name: null,
      surname: null,
      department: null,
      course: null,
      tipology: null,
      year: null,
      matricola: null,
    });
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "include",
      });
    } catch (err) {
      console.error("Logout error:", err);
    } finally {
      if (userInfo) {
        const key = `conversation_${userInfo.matricola || "ospite"}`;
        localStorage.removeItem(key);
      }
      setUserInfo(null);
      setIsAuthenticated(false);
      setConversation([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim()) return;

    setLoading(true);

    // Aggiungi la domanda alla conversazione
    const userMessage = {
      type: "user",
      content: message,
      timestamp: new Date(),
    };
    setConversation((prev) => [...prev, userMessage]);

    const currentQuery = message;
    setMessage(""); // Pulisci l'input subito

    // Ultimi 5 turni (10 messaggi) come contesto conversazionale
    const conversationHistory = conversation
      .filter((msg) => msg.type === "user" || msg.type === "agent")
      .slice(-10)
      .map((msg) => ({
        role: msg.type === "user" ? "user" : "assistant",
        content: msg.content,
      }));

    try {
      const res = await fetch("/api/agent/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
          query: currentQuery,
          user_info: userInfo,
          conversation_history: conversationHistory,
        }),
      });

      const data = await res.json();

      // Aggiungi la risposta alla conversazione
      const agentMessage = {
        type: "agent",
        content: data.response,
        category: data.category,
        metadata: data.metadata,
        timestamp: new Date(),
      };
      setConversation((prev) => [...prev, agentMessage]);
    } catch (error) {
      console.error("Error:", error);
      const errorMessage = {
        type: "error",
        content: "Errore nella comunicazione con il backend",
        timestamp: new Date(),
      };
      setConversation((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleProfileUpdate = (updatedData) => {
    setUserInfo((prev) => ({ ...prev, ...updatedData }));
  };

  const clearConversation = () => {
    setConversation([]);
    if (userInfo) {
      const key = `conversation_${userInfo.matricola || "ospite"}`;
      localStorage.removeItem(key);
    }
  };

  const getCategoryIcon = (category) => {
    const icons = {
      informazioni_corso: "📚",
      orari: "🕐",
      procedure: "📋",
      servizi: "🏛️",
      generale: "💬",
      altro: "❓",
    };
    return icons[category] || "💬";
  };

  const getCategoryLabel = (category) => {
    const labels = {
      informazioni_corso: "Informazioni Corso",
      orari: "Orari",
      procedure: "Procedure",
      servizi: "Servizi",
      generale: "Generale",
      altro: "Altro",
    };
    return labels[category] || category;
  };

  // Renderizza una riga di testo trasformando link Markdown [testo](url) e URL bare in <a> cliccabili
  const renderLineWithLinks = (line) => {
    const regex = /\[([^\]]+)\]\((https?:\/\/[^)]+)\)|(https?:\/\/\S+)/g;
    const parts = [];
    let lastIndex = 0;
    let match;

    while ((match = regex.exec(line)) !== null) {
      if (match.index > lastIndex) {
        parts.push(line.slice(lastIndex, match.index));
      }
      if (match[1] && match[2]) {
        // Link Markdown: [testo](url)
        parts.push(
          <a
            key={match.index}
            href={match[2]}
            target="_blank"
            rel="noopener noreferrer"
          >
            {match[1]}
          </a>,
        );
      } else if (match[3]) {
        // URL nuda — rimuove punteggiatura finale (es. ), ., ,)
        const bareUrl = match[3].replace(/[).,;!?]+$/, "");
        parts.push(
          <a
            key={match.index}
            href={bareUrl}
            target="_blank"
            rel="noopener noreferrer"
          >
            {bareUrl}
          </a>,
        );
        // Rimette nel testo la punteggiatura rimossa
        const trailing = match[3].slice(bareUrl.length);
        if (trailing) parts.push(trailing);
      }
      lastIndex = regex.lastIndex;
    }
    if (lastIndex < line.length) {
      parts.push(line.slice(lastIndex));
    }
    return parts.length > 0 ? parts : line;
  };

  // Show loading screen during initial token verification
  if (isInitialLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h2>Agentic UniBG</h2>
          <p>Caricamento in corso...</p>
        </div>
      </div>
    );
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} onGuest={handleGuest} />;
  }

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-left">
          <img src={unibgLogo} alt="UniBG" className="header-logo" />
        </div>
        <div className="header-center">
          <h1>
            Agentic <span>UniBG</span>
          </h1>
        </div>
        <div className="header-right">
          <div className="user-badge">
            <span className="user-badge-text">
              {userInfo?.status === "loggato"
                ? `${userInfo.name} ${userInfo.surname}`
                : "Ospite"}
            </span>
          </div>
          {userInfo?.status === "loggato" && (
            <button
              className="settings-gear-btn"
              onClick={() => setShowSettings(true)}
              title="Impostazioni"
            >
              ⚙
            </button>
          )}
          <button className="logout-btn" onClick={handleLogout} title="Esci">
            ⏻
          </button>
        </div>
      </header>

      <main className="app-main">
        <div
          className={`conversation-container ${conversation.length === 0 ? "empty" : ""}`}
        >
          {conversation.length === 0 ? (
            <div className="welcome-message">
              <div className="welcome-icon">&#128075;</div>
              <h2>
                {userInfo?.status === "loggato"
                  ? `Ciao, ${userInfo.name}!`
                  : "Ciao!"}
              </h2>
              <p>
                Sono il tuo assistente per l'Università di Bergamo.
                <br />
                Chiedimi qualsiasi cosa!
              </p>
            </div>
          ) : (
            <div className="messages">
              {conversation.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type}`}>
                  {msg.type === "user" && (
                    <div className="message-content user-message">
                      <p>
                        <strong className="msg-sender">&nbsp;</strong>
                        {msg.content}
                      </p>
                    </div>
                  )}
                  {msg.type === "agent" && (
                    <div className="message-content agent-message">
                      {msg.category && (
                        <span className="category-badge">
                          {getCategoryLabel(msg.category)}
                        </span>
                      )}
                      <div className="message-text">
                        {msg.content.split("\n").map((line, i) =>
                          i === 0 ? (
                            <p key={i}>
                              <strong className="msg-sender">
                                &nbsp;&nbsp;
                              </strong>
                              {line ? renderLineWithLinks(line) : "\u00A0"}
                            </p>
                          ) : (
                            <p key={i}>
                              {line ? renderLineWithLinks(line) : "\u00A0"}
                            </p>
                          ),
                        )}
                      </div>
                      {msg.metadata && msg.metadata.workflow_steps && (
                        <details className="workflow-details">
                          <summary>
                            Mostra workflow (
                            {msg.metadata.workflow_steps.length} steps)
                          </summary>
                          <div className="workflow-steps">
                            {msg.metadata.workflow_steps.map((step, i) => (
                              <div key={i} className="workflow-step">
                                <strong>{step.agent}:</strong> {step.step}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  )}
                  {msg.type === "error" && (
                    <div className="message-content error-message">
                      <p>{msg.content}</p>
                    </div>
                  )}
                </div>
              ))}
              {loading && (
                <div className="message agent">
                  <div className="message-content agent-message loading">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={conversationEndRef} />
            </div>
          )}
        </div>

        <div className="input-container">
          <form onSubmit={handleSubmit} className="input-form">
            {conversation.length > 0 && (
              <button
                type="button"
                className="clear-btn"
                onClick={clearConversation}
                title="Pulisci conversazione"
              >
                🗑
              </button>
            )}
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Scrivi la tua domanda qui..."
              rows="1"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              onInput={(e) => {
                e.target.style.height = "auto";
                e.target.style.height =
                  Math.min(e.target.scrollHeight, 120) + "px";
              }}
            />
            <button
              type="submit"
              className={`send-btn ${message.trim() && !loading ? "active" : ""}`}
              disabled={loading || !message.trim()}
              title="Invia"
            >
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M8 14V3"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
                <path
                  d="M3 7L8 2L13 7"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </form>
        </div>
      </main>

      {showSettings && (
        <SettingsPage
          userInfo={userInfo}
          connectionStatus={connectionStatus}
          onClose={() => setShowSettings(false)}
          onProfileUpdate={handleProfileUpdate}
        />
      )}
    </div>
  );
}

export default App;
