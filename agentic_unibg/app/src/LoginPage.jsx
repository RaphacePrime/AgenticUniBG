import { useState, useMemo } from "react";
import "./LoginPage.css";

const DIPARTIMENTI_CORSI = {
  "CIS - Corsi di Italiano per Stranieri": [
    { nome: "Corsi intensivi (c.int)", tipo: "Corsi CIS" },
    { nome: "Corso italiano per stranieri (cis)", tipo: "Corsi CIS" },
  ],
  "Dipartimento di Giurisprudenza": [
    {
      nome: "Giurisprudenza",
      tipo: "Laurea Magistrale a ciclo unico (5 anni)",
    },
    {
      nome: "Giurisprudenza (riservato agli Allievi della Guardia di Finanza)",
      tipo: "Laurea Magistrale a ciclo unico (5 anni)",
    },
    {
      nome: "Diritto per l'impresa nazionale e internazionale",
      tipo: "Laurea",
    },
    {
      nome: "Diritti umani, migrazioni e cooperazione internazionale",
      tipo: "Laurea Magistrale",
    },
  ],
  "Dipartimento di Lettere, Filosofia, Comunicazione": [
    { nome: "Lettere", tipo: "Laurea" },
    { nome: "Filosofia", tipo: "Laurea" },
    { nome: "Filosofia, Scienze e Società", tipo: "Laurea Magistrale" },
    {
      nome: "Philosophical Knowledge: Foundations, Methods, Applications",
      tipo: "Laurea Magistrale",
    },
    { nome: "Culture umanistiche", tipo: "Laurea Magistrale" },
    {
      nome: "Comunicazione, Informazione, Editoria",
      tipo: "Laurea Magistrale",
    },
    { nome: "Scienze della comunicazione", tipo: "Laurea" },
    {
      nome: "Text Sciences and Culture Enhancement in the Digital Age",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Valorizzazione del patrimonio culturale materiale e immateriale",
      tipo: "Laurea Magistrale",
    },
  ],
  "Dipartimento di Lingue, Letterature e Culture Straniere": [
    { nome: "Lingue e letterature straniere moderne", tipo: "Laurea" },
    {
      nome: "Lingue moderne per la comunicazione e la cooperazione internazionale",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Intercultural Studies in Languages and Literatures",
      tipo: "Laurea Magistrale",
    },
  ],
  "Dipartimento di Scienze Aziendali": [
    { nome: "Economia aziendale", tipo: "Laurea" },
    {
      nome: "Economia aziendale, direzione amministrativa e professione",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "International Management and Marketing",
      tipo: "Laurea Magistrale",
    },
    { nome: "Management, Innovazione e Finanza", tipo: "Laurea Magistrale" },
    {
      nome: "Accounting, Governance and Sustainability",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Welfare Management e Innovazione Sociale",
      tipo: "Laurea Magistrale",
    },
  ],
  "Dipartimento di Scienze Economiche": [
    { nome: "Economia", tipo: "Laurea" },
    { nome: "Economics and Finance", tipo: "Laurea Magistrale" },
    { nome: "Economics and Data Analysis", tipo: "Laurea Magistrale" },
    { nome: "Data Analytics, Economia e Tecnologie Digitali", tipo: "Laurea" },
    {
      nome: "Geopolitica, Economia e Strategie Globali",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Planning and Management of Tourism Systems",
      tipo: "Laurea Magistrale",
    },
  ],
  "Dipartimento di Scienze Umane e Sociali": [
    { nome: "Scienze dell'educazione", tipo: "Laurea" },
    { nome: "Scienze pedagogiche", tipo: "Laurea Magistrale" },
    {
      nome: "Scienze della formazione primaria",
      tipo: "Laurea Magistrale a ciclo unico (5 anni)",
    },
    { nome: "Scienze psicologiche", tipo: "Laurea" },
    { nome: "Psicologia clinica", tipo: "Laurea Magistrale" },
    {
      nome: "Clinical Psychology for Individuals, Families and Organizations",
      tipo: "Laurea Magistrale",
    },
    { nome: "Scienze politiche e strategie globali", tipo: "Laurea" },
    { nome: "Scienze motorie e sportive", tipo: "Laurea" },
    {
      nome: "Scienze, metodi e didattiche delle attività sportive",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Progettazione di contesti di vita accessibili ed inclusivi",
      tipo: "Laurea Magistrale",
    },
  ],
  "Scuola di Ingegneria": [
    { nome: "Ingegneria gestionale", tipo: "Laurea" },
    { nome: "Ingegneria gestionale", tipo: "Laurea Magistrale" },
    { nome: "Management Engineering", tipo: "Laurea Magistrale" },
    { nome: "Ingegneria informatica", tipo: "Laurea" },
    { nome: "Ingegneria informatica", tipo: "Laurea Magistrale" },
    { nome: "Ingegneria meccanica", tipo: "Laurea" },
    { nome: "Ingegneria meccanica", tipo: "Laurea Magistrale" },
    { nome: "Ingegneria delle costruzioni edili", tipo: "Laurea Magistrale" },
    { nome: "Ingegneria delle tecnologie per l'edilizia", tipo: "Laurea" },
    {
      nome: "Ingegneria delle tecnologie per l'elettronica e l'automazione",
      tipo: "Laurea",
    },
    { nome: "Ingegneria delle tecnologie per la salute", tipo: "Laurea" },
    { nome: "Medical Engineering", tipo: "Laurea Magistrale" },
    {
      nome: "Engineering and Management for Health",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Mechatronics and Smart Technology Engineering",
      tipo: "Laurea Magistrale",
    },
    {
      nome: "Ingegneria delle tecnologie per la sostenibilità energetica e ambientale",
      tipo: "Laurea",
    },
    {
      nome: "Geourbanistica. Analisi e pianificazione territoriale, urbana, ambientale e valorizzazione del paesaggio",
      tipo: "Laurea Magistrale",
    },
  ],
};

function LoginPage({ onLogin, onGuest }) {
  const [activeTab, setActiveTab] = useState("login");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  // Login form state
  const [loginData, setLoginData] = useState({
    matricola: "",
    password: "",
  });

  // Register form state
  const [registerData, setRegisterData] = useState({
    name: "",
    surname: "",
    matricola: "",
    password: "",
    confirmPassword: "",
    department: "",
    course: "",
    tipology: "Triennale",
    year: 1,
  });

  const [selectedCourseIndex, setSelectedCourseIndex] = useState("");

  // Calcola i corsi disponibili in base al dipartimento selezionato
  const availableCourses = useMemo(() => {
    if (!registerData.department) {
      // Se non c'è un dipartimento selezionato, mostra tutti i corsi
      return Object.entries(DIPARTIMENTI_CORSI).flatMap(([dept, courses]) =>
        courses.map((course) => ({ ...course, department: dept })),
      );
    }
    // Altrimenti mostra solo i corsi del dipartimento selezionato
    return (DIPARTIMENTI_CORSI[registerData.department] || []).map(
      (course) => ({ ...course, department: registerData.department }),
    );
  }, [registerData.department]);

  // Quando cambia il dipartimento, resetta il corso se non è più disponibile
  const handleDepartmentChange = (newDepartment) => {
    setSelectedCourseIndex("");
    setRegisterData((prev) => {
      return {
        ...prev,
        department: newDepartment,
        course: "",
        tipology: "Altro",
        year: 1,
      };
    });
  };

  // Quando cambia il corso, imposta automaticamente tipologia e anno
  const handleCourseChange = (courseIndex) => {
    if (!courseIndex) {
      setRegisterData((prev) => ({
        ...prev,
        course: "",
        tipology: "Altro",
        year: 1,
      }));
      return;
    }

    const selectedCourse = availableCourses[parseInt(courseIndex)];

    let tipology = "Altro";
    let year = 1;

    if (selectedCourse) {
      // Determina la tipologia in base al tipo di corso
      if (selectedCourse.tipo === "Laurea") {
        tipology = "Triennale";
        year = 1;
      } else if (selectedCourse.tipo === "Laurea Magistrale") {
        tipology = "Magistrale";
        year = 1;
      } else if (selectedCourse.tipo.includes("ciclo unico")) {
        tipology = "Ciclo Unico";
        year = 1;
      }

      setRegisterData((prev) => ({
        ...prev,
        course: selectedCourse.nome,
        tipology: tipology,
        year: year,
      }));
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          matricola: loginData.matricola,
          password: loginData.password,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Errore nel login");
      }
      const userData = await res.json();
      onLogin(userData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    if (registerData.password !== registerData.confirmPassword) {
      setError("Le password non coincidono");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name: registerData.name,
          surname: registerData.surname,
          matricola: registerData.matricola,
          password: registerData.password,
          department: registerData.department,
          course: registerData.course,
          tipology: registerData.tipology,
          year: parseInt(registerData.year),
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Errore nella registrazione");
      }
      const userData = await res.json();
      onLogin(userData);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-container">
        {/* ── Left Panel: Login / Register ── */}
        <div className="auth-panel">
          <div className="auth-brand">
            <span className="brand-icon">🎓</span>
            <h1>Agentic UniBG</h1>
          </div>

          {/* Tabs */}
          <div className="auth-tabs">
            <button
              className={`auth-tab ${activeTab === "login" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("login");
                setError("");
              }}
            >
              Accedi
            </button>
            <button
              className={`auth-tab ${activeTab === "register" ? "active" : ""}`}
              onClick={() => {
                setActiveTab("register");
                setError("");
              }}
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
          {activeTab === "login" && (
            <form onSubmit={handleLogin} className="auth-form">
              <div className="form-group">
                <label htmlFor="login-matricola">Matricola</label>
                <input
                  id="login-matricola"
                  type="text"
                  value={loginData.matricola}
                  onChange={(e) =>
                    setLoginData({ ...loginData, matricola: e.target.value })
                  }
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
                  onChange={(e) =>
                    setLoginData({ ...loginData, password: e.target.value })
                  }
                  placeholder="••••••••"
                  required
                />
              </div>
              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="btn-spinner"></span> Accesso in corso...
                  </>
                ) : (
                  "Accedi"
                )}
              </button>
            </form>
          )}

          {/* Register Form */}
          {activeTab === "register" && (
            <form onSubmit={handleRegister} className="auth-form register-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-name">Nome</label>
                  <input
                    id="reg-name"
                    type="text"
                    value={registerData.name}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, name: e.target.value })
                    }
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
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        surname: e.target.value,
                      })
                    }
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
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        matricola: e.target.value,
                      })
                    }
                    placeholder="123456"
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="reg-department">Dipartimento</label>
                  <select
                    id="reg-department"
                    value={registerData.department}
                    onChange={(e) => handleDepartmentChange(e.target.value)}
                    required
                  >
                    <option value="">Seleziona un dipartimento</option>
                    {Object.keys(DIPARTIMENTI_CORSI).map((dept) => (
                      <option key={dept} value={dept}>
                        {dept}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-course">Corso di Laurea</label>
                  <select
                    id="reg-course"
                    value={selectedCourseIndex}
                    onChange={(e) => {
                      setSelectedCourseIndex(e.target.value);
                      handleCourseChange(e.target.value);
                    }}
                    required
                  >
                    <option value="">Seleziona un corso</option>
                    {availableCourses.map((course, index) => (
                      <option
                        key={`${course.nome}-${course.tipo}-${index}`}
                        value={index}
                      >
                        {course.nome} - {course.tipo}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="reg-tipology">Tipologia</label>
                  <select
                    id="reg-tipology"
                    value={registerData.tipology}
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        tipology: e.target.value,
                      })
                    }
                    disabled
                  >
                    <option value="Triennale">Triennale</option>
                    <option value="Magistrale">Magistrale</option>
                    <option value="Ciclo Unico">Ciclo Unico</option>
                    <option value="Altro">Altro</option>
                  </select>
                </div>
                <div className="form-group">
                  <label htmlFor="reg-year">Anno</label>
                  <select
                    id="reg-year"
                    value={registerData.year}
                    onChange={(e) =>
                      setRegisterData({ ...registerData, year: e.target.value })
                    }
                  >
                    {registerData.tipology === "Triennale" && (
                      <>
                        <option value={1}>1° Anno</option>
                        <option value={2}>2° Anno</option>
                        <option value={3}>3° Anno</option>
                      </>
                    )}
                    {registerData.tipology === "Magistrale" && (
                      <>
                        <option value={1}>1° Anno</option>
                        <option value={2}>2° Anno</option>
                      </>
                    )}
                    {registerData.tipology === "Ciclo Unico" && (
                      <>
                        <option value={1}>1° Anno</option>
                        <option value={2}>2° Anno</option>
                        <option value={3}>3° Anno</option>
                        <option value={4}>4° Anno</option>
                        <option value={5}>5° Anno</option>
                      </>
                    )}
                    {registerData.tipology === "Altro" && (
                      <>
                        <option value={1}>1° Anno</option>
                        <option value={2}>2° Anno</option>
                        <option value={3}>3° Anno</option>
                        <option value={4}>4° Anno</option>
                        <option value={5}>5° Anno</option>
                      </>
                    )}
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
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        password: e.target.value,
                      })
                    }
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
                    onChange={(e) =>
                      setRegisterData({
                        ...registerData,
                        confirmPassword: e.target.value,
                      })
                    }
                    placeholder="••••••••"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                className="auth-submit-btn"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="btn-spinner"></span> Registrazione...
                  </>
                ) : (
                  "Registrati"
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
              Esplora i servizi dell'università senza effettuare la
              registrazione
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
              Le risposte saranno generiche.
              <br />
              Per un'esperienza personalizzata, accedi o registrati.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
