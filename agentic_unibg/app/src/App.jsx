import { useState, useEffect } from 'react'
import './App.css'
import LoginPage from './LoginPage'

function App() {
  const [message, setMessage] = useState('')
  const [conversation, setConversation] = useState([])
  const [loading, setLoading] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('checking')
  const [showWorkflow, setShowWorkflow] = useState(false)

  // Auth state
  const [userInfo, setUserInfo] = useState(null) // null = not logged in, show login page
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isInitialLoading, setIsInitialLoading] = useState(true)

  useEffect(() => {
    // Test connection to backend
    fetch('/api/health')
      .then(res => res.json())
      .then(data => {
        console.log('Backend status:', data)
        setConnectionStatus('connected')
      })
      .catch(err => {
        console.error('Backend connection error:', err)
        setConnectionStatus('error')
      })
    
    // Verifica token dal cookie
    fetch('/api/auth/verify', {
      credentials: 'include'
    })
      .then(res => {
        if (!res.ok) throw new Error('Token invalido')
        return res.json()
      })
      .then(userData => {
        setUserInfo(userData)
        setIsAuthenticated(true)
      })
      .catch(err => {
        console.error('Token verification failed:', err)
      })
      .finally(() => {
        setIsInitialLoading(false)
      })
  }, [])

  // Auth handlers
  const handleLogin = (userData) => {
    setUserInfo(userData)
    setIsAuthenticated(true)
  }

  const handleGuest = () => {
    setUserInfo({
      status: 'ospite',
      name: null,
      surname: null,
      department: null,
      course: null,
      tipology: null,
      year: null,
      matricola: null,
    })
    setIsAuthenticated(true)
  }

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'include'
      })
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setUserInfo(null)
      setIsAuthenticated(false)
      setConversation([])
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!message.trim()) return
    
    setLoading(true)
    
    // Aggiungi la domanda alla conversazione
    const userMessage = { type: 'user', content: message, timestamp: new Date() }
    setConversation(prev => [...prev, userMessage])
    
    const currentQuery = message
    setMessage('') // Pulisci l'input subito
    
    try {
      const res = await fetch('/api/agent/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ query: currentQuery, user_info: userInfo })
      })
      
      const data = await res.json()
      
      // Aggiungi la risposta alla conversazione
      const agentMessage = {
        type: 'agent',
        content: data.response,
        category: data.category,
        metadata: data.metadata,
        timestamp: new Date()
      }
      setConversation(prev => [...prev, agentMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage = {
        type: 'error',
        content: 'Errore nella comunicazione con il backend',
        timestamp: new Date()
      }
      setConversation(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const clearConversation = () => {
    setConversation([])
  }

  const getCategoryIcon = (category) => {
    const icons = {
      'informazioni_corso': '📚',
      'orari': '🕐',
      'procedure': '📋',
      'servizi': '🏛️',
      'generale': '💬',
      'altro': '❓'
    }
    return icons[category] || '💬'
  }

  const getCategoryLabel = (category) => {
    const labels = {
      'informazioni_corso': 'Informazioni Corso',
      'orari': 'Orari',
      'procedure': 'Procedure',
      'servizi': 'Servizi',
      'generale': 'Generale',
      'altro': 'Altro'
    }
    return labels[category] || category
  }

  // Show loading screen during initial token verification
  if (isInitialLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-content">
          <div className="loading-spinner"></div>
          <h2>🎓 Agentic UniBG</h2>
          <p>Caricamento in corso...</p>
        </div>
      </div>
    )
  }

  // Show login page if not authenticated
  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} onGuest={handleGuest} />
  }

  return (
    <div className="App">
      <header className="app-header">
        <div className="header-content">
          <h1>🎓 Agentic UniBG</h1>
          <p className="subtitle">Assistente Intelligente per l'Università di Bergamo</p>
        </div>
        <div className="header-right">
          <div className="user-badge">
            {userInfo?.status === 'loggato' ? (
              <>
                <span className="user-badge-icon">🎓</span>
                <span className="user-badge-text">{userInfo.name} {userInfo.surname}</span>
              </>
            ) : (
              <>
                <span className="user-badge-icon">👤</span>
                <span className="user-badge-text">Ospite</span>
              </>
            )}
          </div>
          <div className="connection-status">
            <span className={`status-indicator ${connectionStatus}`}></span>
            {connectionStatus === 'connected' ? 'Connesso' : connectionStatus === 'error' ? 'Disconnesso' : 'Connessione...'}
          </div>
          <button className="logout-btn" onClick={handleLogout}>Esci</button>
        </div>
      </header>

      <main className="app-main">
        <div className="conversation-container">
          {conversation.length === 0 ? (
            <div className="welcome-message">
              <h2>
                {userInfo?.status === 'loggato'
                  ? `Benvenuto, ${userInfo.name}! 👋`
                  : 'Benvenuto! 👋'}
              </h2>
              <p>Sono il tuo assistente per l'Università di Bergamo.</p>
              {userInfo?.status === 'loggato' && (
                <p className="welcome-user-info">
                  📋 {userInfo.course} &bull; {userInfo.tipology} &bull; {userInfo.year}° Anno &bull; {userInfo.department}
                </p>
              )}
              <p>Puoi chiedermi informazioni su:</p>
              <ul>
                <li>📚 Corsi e programmi di studio</li>
                <li>🕐 Orari delle lezioni e degli esami</li>
                <li>📋 Procedure amministrative</li>
                <li>🏛️ Servizi universitari</li>
              </ul>
            </div>
          ) : (
            <div className="messages">
              {conversation.map((msg, idx) => (
                <div key={idx} className={`message ${msg.type}`}>
                  {msg.type === 'user' && (
                    <div className="message-content user-message">
                      <div className="message-header">
                        <span className="user-icon">👤</span>
                        <span className="message-label">Tu</span>
                      </div>
                      <p>{msg.content}</p>
                    </div>
                  )}
                  {msg.type === 'agent' && (
                    <div className="message-content agent-message">
                      <div className="message-header">
                        <span className="agent-icon">🤖</span>
                        <span className="message-label">Assistente</span>
                        {msg.category && (
                          <span className="category-badge">
                            {getCategoryIcon(msg.category)} {getCategoryLabel(msg.category)}
                          </span>
                        )}
                      </div>
                      <p>{msg.content}</p>
                      {msg.metadata && msg.metadata.workflow_steps && (
                        <details className="workflow-details">
                          <summary>Mostra workflow ({msg.metadata.workflow_steps.length} steps)</summary>
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
                  {msg.type === 'error' && (
                    <div className="message-content error-message">
                      <span className="error-icon">⚠️</span>
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
            </div>
          )}
        </div>

        <div className="input-container">
          {conversation.length > 0 && (
            <button className="clear-btn" onClick={clearConversation}>
              🗑️ Pulisci conversazione
            </button>
          )}
          <form onSubmit={handleSubmit} className="input-form">
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Scrivi la tua domanda qui..."
              rows="3"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            <button type="submit" disabled={loading || !message.trim()}>
              {loading ? '⏳ Elaborazione...' : '📤 Invia'}
            </button>
          </form>
          <p className="input-hint">Premi Enter per inviare, Shift+Enter per andare a capo</p>
        </div>
      </main>
    </div>
  )
}

export default App
