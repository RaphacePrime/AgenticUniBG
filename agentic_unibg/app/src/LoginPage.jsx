import { useState } from 'react'
import './LoginPage.css'

function LoginPage({ onLogin, onGuest }) {
  const [activeTab, setActiveTab] = useState('login')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Login form state
  const [loginData, setLoginData] = useState({
    matricola: '',
    password: ''
  })

  // Register form state
  const [registerData, setRegisterData] = useState({
    name: '',
    surname: '',
    matricola: '',
    password: '',
    confirmPassword: '',
    department: '',
    course: '',
    tipology: 'Triennale',
    year: 1
  })

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          matricola: loginData.matricola,
          password: loginData.password
        })
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Errore nel login')
      }
      const userData = await res.json()
      onLogin(userData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    if (registerData.password !== registerData.confirmPassword) {
      setError('Le password non coincidono')
      setLoading(false)
      return
    }

    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: registerData.name,
          surname: registerData.surname,
          matricola: registerData.matricola,
          password: registerData.password,
          department: registerData.department,
          course: registerData.course,
          tipology: registerData.tipology,
          year: parseInt(registerData.year)
        })
      })
      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || 'Errore nella registrazione')
      }
      const userData = await res.json()
      onLogin(userData)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="login-page">
      <div className="login-container">
        {/* ── Left Panel: Login / Register ── */}
        <div className="auth-panel">
          <div className="auth-brand">
            <span className="brand-icon">🎓</span>
            <h1>Agentic UniBG</h1>
            <p>Assistente Intelligente per l'Università di Bergamo</p>
          </div>

          {/* Tabs */}
          <div className="auth-tabs">
            <button
              className={`auth-tab ${activeTab === 'login' ? 'active' : ''}`}
              onClick={() => { setActiveTab('login'); setError('') }}
            >
              Accedi
            </button>
            <button
              className={`auth-tab ${activeTab === 'register' ? 'active' : ''}`}
              onClick={() => { setActiveTab('register'); setError('') }}
            >
              Registrati
            </button>
          </div>

          {error && (
            <div className="auth-error">
              <span>⚠️</span> {error}
            </div>
          )}

          {/* Login Form */}
          {activeTab === 'login' && (
            <form onSubmit={handleLogin} className="auth-form">
              <div className="form-group">
                <label htmlFor="login-matricola">Matricola</label>
                <input
                  id="login-matricola"
                  type="text"
                  value={loginData.matricola}
                  onChange={e => setLoginData({ ...loginData, matricola: e.target.value })}
                  placeholder="Es: 123456"
                  required
                  autoFocus
                />
              </div>
              <div className="form-group">
                <label htmlFor="login-password">Password</label>
                <input
                  id="login-password"
                  type="password"
                  value={loginData.password}
                  onChange={e => setLoginData({ ...loginData, password: e.target.value })}
                  placeholder="••••••••"
                  required
                />
              </div>
              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? (
                  <><span className="btn-spinner"></span> Accesso in corso...</>
                ) : (
                  'Accedi'
                )}
              </button>
            </form>
          )}

          {/* Register Form */}
          {activeTab === 'register' && (
            <form onSubmit={handleRegister} className="auth-form register-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-name">Nome</label>
                  <input
                    id="reg-name"
                    type="text"
                    value={registerData.name}
                    onChange={e => setRegisterData({ ...registerData, name: e.target.value })}
                    placeholder="Mario"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-surname">Cognome</label>
                  <input
                    id="reg-surname"
                    type="text"
                    value={registerData.surname}
                    onChange={e => setRegisterData({ ...registerData, surname: e.target.value })}
                    placeholder="Rossi"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-matricola">Matricola</label>
                  <input
                    id="reg-matricola"
                    type="text"
                    value={registerData.matricola}
                    onChange={e => setRegisterData({ ...registerData, matricola: e.target.value })}
                    placeholder="123456"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-department">Dipartimento</label>
                  <input
                    id="reg-department"
                    type="text"
                    value={registerData.department}
                    onChange={e => setRegisterData({ ...registerData, department: e.target.value })}
                    placeholder="Dip. di Ingegneria"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-course">Corso di Laurea</label>
                  <input
                    id="reg-course"
                    type="text"
                    value={registerData.course}
                    onChange={e => setRegisterData({ ...registerData, course: e.target.value })}
                    placeholder="Ingegneria Informatica"
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-tipology">Tipologia</label>
                  <select
                    id="reg-tipology"
                    value={registerData.tipology}
                    onChange={e => setRegisterData({ ...registerData, tipology: e.target.value })}
                  >
                    <option value="Triennale">Triennale</option>
                    <option value="Magistrale">Magistrale</option>
                    <option value="Ciclo Unico">Ciclo Unico</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="reg-year">Anno</label>
                  <select
                    id="reg-year"
                    value={registerData.year}
                    onChange={e => setRegisterData({ ...registerData, year: e.target.value })}
                  >
                    <option value={1}>1° Anno</option>
                    <option value={2}>2° Anno</option>
                    <option value={3}>3° Anno</option>
                    <option value={4}>4° Anno</option>
                    <option value={5}>5° Anno</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-password">Password</label>
                  <input
                    id="reg-password"
                    type="password"
                    value={registerData.password}
                    onChange={e => setRegisterData({ ...registerData, password: e.target.value })}
                    placeholder="••••••••"
                    required
                    minLength={6}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-confirm">Conferma Password</label>
                  <input
                    id="reg-confirm"
                    type="password"
                    value={registerData.confirmPassword}
                    onChange={e => setRegisterData({ ...registerData, confirmPassword: e.target.value })}
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <button type="submit" className="auth-submit-btn" disabled={loading}>
                {loading ? (
                  <><span className="btn-spinner"></span> Registrazione...</>
                ) : (
                  'Registrati'
                )}
              </button>
            </form>
          )}
        </div>

        {/* ── Divider ── */}
        <div className="auth-divider">
          <div className="divider-line"></div>
          <span className="divider-text">oppure</span>
          <div className="divider-line"></div>
        </div>

        {/* ── Right Panel: Guest ── */}
        <div className="guest-panel">
          <div className="guest-content">
            <div className="guest-illustration">
              <div className="guest-avatar">👤</div>
              <div className="guest-glow"></div>
            </div>

            <h2>Accesso Ospite</h2>
            <p className="guest-description">
              Esplora i servizi dell'università senza effettuare la registrazione
            </p>

            <ul className="guest-features">
              <li>
                <span className="feature-icon">💬</span>
                <span>Chatta con l'assistente AI</span>
              </li>
              <li>
                <span className="feature-icon">📚</span>
                <span>Esplora corsi e programmi</span>
              </li>
              <li>
                <span className="feature-icon">🏛️</span>
                <span>Informazioni sui servizi</span>
              </li>
              <li>
                <span className="feature-icon">🕐</span>
                <span>Consulta orari e date</span>
              </li>
            </ul>

            <button className="guest-btn" onClick={onGuest}>
              Continua come Ospite
              <span className="guest-btn-arrow">→</span>
            </button>

            <p className="guest-note">
              Le risposte saranno generiche.<br/>
              Per un'esperienza personalizzata, accedi o registrati.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
