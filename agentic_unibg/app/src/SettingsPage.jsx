import { useState, useMemo } from "react";
import "./SettingsPage.css";

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

// Mappa tipo corso -> tipologia
const tipoToTipology = (tipo) => {
  if (tipo === "Laurea") return "Triennale";
  if (tipo === "Laurea Magistrale") return "Magistrale";
  if (tipo && tipo.includes("ciclo unico")) return "Ciclo Unico";
  return "Altro";
};

// Mappa tipologia -> tipo corso (inversa)
const tipologyToTipo = (tipology) => {
  if (tipology === "Triennale") return "Laurea";
  if (tipology === "Magistrale") return "Laurea Magistrale";
  if (tipology === "Ciclo Unico")
    return "Laurea Magistrale a ciclo unico (5 anni)";
  return null;
};

function SettingsPage({
  userInfo,
  connectionStatus,
  onClose,
  onProfileUpdate,
}) {
  const [profileData, setProfileData] = useState({
    name: userInfo?.name || "",
    surname: userInfo?.surname || "",
    department: userInfo?.department || "",
    course: userInfo?.course || "",
    tipology: userInfo?.tipology || "",
    year: userInfo?.year || 1,
  });

  const [selectedCourseIndex, setSelectedCourseIndex] = useState("");

  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  const [profileMsg, setProfileMsg] = useState({ type: "", text: "" });
  const [passwordMsg, setPasswordMsg] = useState({ type: "", text: "" });
  const [profileLoading, setProfileLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Corsi disponibili in base al dipartimento
  const availableCourses = useMemo(() => {
    if (!profileData.department) return [];
    return (DIPARTIMENTI_CORSI[profileData.department] || []).map((course) => ({
      ...course,
      department: profileData.department,
    }));
  }, [profileData.department]);

  // Trova l'indice iniziale del corso dal profilo utente
  useMemo(() => {
    if (
      availableCourses.length > 0 &&
      profileData.course &&
      selectedCourseIndex === ""
    ) {
      const expectedTipo = tipologyToTipo(profileData.tipology);
      const idx = availableCourses.findIndex(
        (c) =>
          c.nome === profileData.course &&
          (expectedTipo ? c.tipo === expectedTipo : true),
      );
      if (idx !== -1) {
        setSelectedCourseIndex(String(idx));
      }
    }
  }, [availableCourses]);

  const handleDepartmentChange = (newDepartment) => {
    setSelectedCourseIndex("");
    setProfileData((prev) => ({
      ...prev,
      department: newDepartment,
      course: "",
      tipology: "Altro",
      year: 1,
    }));
  };

  const handleCourseChange = (courseIndex) => {
    if (!courseIndex) {
      setSelectedCourseIndex("");
      setProfileData((prev) => ({
        ...prev,
        course: "",
        tipology: "Altro",
        year: 1,
      }));
      return;
    }

    setSelectedCourseIndex(courseIndex);
    const selectedCourse = availableCourses[parseInt(courseIndex)];

    if (selectedCourse) {
      const tipology = tipoToTipology(selectedCourse.tipo);
      setProfileData((prev) => ({
        ...prev,
        course: selectedCourse.nome,
        tipology,
        year: 1,
      }));
    }
  };

  const getMaxYear = () => {
    if (profileData.tipology === "Triennale") return 3;
    if (profileData.tipology === "Magistrale") return 2;
    if (profileData.tipology === "Ciclo Unico") return 5;
    return 5;
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileMsg({ type: "", text: "" });

    try {
      const res = await fetch("/api/auth/profile", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(profileData),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Errore aggiornamento profilo");
      }
      const updated = await res.json();
      setProfileMsg({
        type: "success",
        text: "Profilo aggiornato con successo!",
      });
      if (onProfileUpdate) onProfileUpdate(updated);
    } catch (err) {
      setProfileMsg({ type: "error", text: err.message });
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordMsg({ type: "", text: "" });

    if (passwordData.newPassword.length < 6) {
      setPasswordMsg({
        type: "error",
        text: "La nuova password deve essere di almeno 6 caratteri",
      });
      return;
    }
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordMsg({ type: "error", text: "Le password non coincidono" });
      return;
    }

    setPasswordLoading(true);
    try {
      const res = await fetch("/api/auth/password", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          current_password: passwordData.currentPassword,
          new_password: passwordData.newPassword,
        }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Errore cambio password");
      }
      setPasswordMsg({
        type: "success",
        text: "Password aggiornata con successo!",
      });
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (err) {
      setPasswordMsg({ type: "error", text: err.message });
    } finally {
      setPasswordLoading(false);
    }
  };

  return (
    <div className="settings-overlay">
      <div className="settings-panel">
        <div className="settings-header">
          <h2>Impostazioni</h2>
          <button
            className="settings-close-btn"
            onClick={onClose}
            title="Chiudi"
          >
            ✕
          </button>
        </div>

        <div className="settings-body">
          {/* Stato Server */}
          <div className="settings-section server-status-section">
            <h3>Stato del Server</h3>
            <div className="server-status-row">
              <span className={`status-dot ${connectionStatus}`}></span>
              <span className="server-status-text">
                {connectionStatus === "connected"
                  ? "Connesso"
                  : connectionStatus === "error"
                    ? "Disconnesso"
                    : "Connessione..."}
              </span>
            </div>
          </div>

          {/* Dati Profilo */}
          <div className="settings-section">
            <h3>Dati Profilo</h3>
            <form onSubmit={handleProfileSubmit} className="settings-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Nome</label>
                  <input
                    type="text"
                    value={profileData.name}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        name: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Cognome</label>
                  <input
                    type="text"
                    value={profileData.surname}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        surname: e.target.value,
                      }))
                    }
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Dipartimento</label>
                <select
                  value={profileData.department}
                  onChange={(e) => handleDepartmentChange(e.target.value)}
                  required
                >
                  <option value="">Seleziona dipartimento</option>
                  {Object.keys(DIPARTIMENTI_CORSI).map((dept) => (
                    <option key={dept} value={dept}>
                      {dept}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Corso di Laurea</label>
                <select
                  value={selectedCourseIndex}
                  onChange={(e) => handleCourseChange(e.target.value)}
                  required
                  disabled={!profileData.department}
                >
                  <option value="">Seleziona corso</option>
                  {availableCourses.map((c, i) => (
                    <option key={i} value={String(i)}>
                      {c.nome} ({c.tipo})
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Tipologia</label>
                  <input
                    type="text"
                    value={profileData.tipology}
                    readOnly
                    className="readonly-input"
                  />
                </div>
                <div className="form-group">
                  <label>Anno</label>
                  <select
                    value={profileData.year}
                    onChange={(e) =>
                      setProfileData((prev) => ({
                        ...prev,
                        year: parseInt(e.target.value),
                      }))
                    }
                    required
                  >
                    {Array.from({ length: getMaxYear() }, (_, i) => i + 1).map(
                      (y) => (
                        <option key={y} value={y}>
                          {y}° anno
                        </option>
                      ),
                    )}
                  </select>
                </div>
              </div>

              {profileMsg.text && (
                <div className={`settings-msg ${profileMsg.type}`}>
                  {profileMsg.text}
                </div>
              )}

              <button
                type="submit"
                className="settings-save-btn"
                disabled={profileLoading}
              >
                {profileLoading ? "Salvataggio..." : "Salva Modifiche"}
              </button>
            </form>
          </div>

          {/* Cambia Password */}
          <div className="settings-section">
            <h3>Cambia Password</h3>
            <form onSubmit={handlePasswordSubmit} className="settings-form">
              <div className="form-group">
                <label>Password Corrente</label>
                <input
                  type="password"
                  value={passwordData.currentPassword}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      currentPassword: e.target.value,
                    }))
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>Nuova Password</label>
                <input
                  type="password"
                  value={passwordData.newPassword}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      newPassword: e.target.value,
                    }))
                  }
                  required
                  minLength={6}
                />
              </div>
              <div className="form-group">
                <label>Conferma Nuova Password</label>
                <input
                  type="password"
                  value={passwordData.confirmPassword}
                  onChange={(e) =>
                    setPasswordData((prev) => ({
                      ...prev,
                      confirmPassword: e.target.value,
                    }))
                  }
                  required
                  minLength={6}
                />
              </div>

              {passwordMsg.text && (
                <div className={`settings-msg ${passwordMsg.type}`}>
                  {passwordMsg.text}
                </div>
              )}

              <button
                type="submit"
                className="settings-save-btn"
                disabled={passwordLoading}
              >
                {passwordLoading ? "Aggiornamento..." : "Cambia Password"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsPage;
