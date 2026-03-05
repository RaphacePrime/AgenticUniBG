import os
from datetime import datetime
from typing import Dict, List, Optional


class PipelineLogger:
    """
    Logger che crea un file di log dettagliato per ogni query utente,
    catturando l'intera pipeline: Classifier → QueryAgent → WebAgent → Generator → Reviser.
    """

    LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

    def __init__(self):
        os.makedirs(self.LOGS_DIR, exist_ok=True)

    def _build_filename(self, matricola: Optional[str], timestamp: datetime) -> str:
        """
        Costruisce il nome del file di log: log_{matricola}_{timestamp} oppure log_ospite_{timestamp}
        """
        user_id = matricola if matricola else "ospite"
        ts = timestamp.strftime("%Y%m%d_%H%M%S_%f")
        return f"log_{user_id}_{ts}.txt"

    def write_log(self, state: Dict, workflow_steps: List[Dict], timestamp: datetime = None, total_time: float = None) -> str:
        """
        Scrive il file di log completo della pipeline e restituisce il percorso del file.
        """
        if timestamp is None:
            timestamp = datetime.now()

        matricola = state.get("user_matricola")
        filename = self._build_filename(matricola, timestamp)
        filepath = os.path.join(self.LOGS_DIR, filename)

        lines = self._build_log_content(state, workflow_steps, timestamp, total_time)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath

    def _build_log_content(self, state: Dict, workflow_steps: List[Dict], timestamp: datetime, total_time: float = None) -> List[str]:
        """
        Costruisce il contenuto completo del log come lista di righe.
        """
        sep = "=" * 80
        sub_sep = "-" * 60
        lines = []

        # ── Intestazione ──
        lines.append(sep)
        lines.append("AGENTIC UNIBG - PIPELINE LOG")
        lines.append(sep)
        lines.append(f"Timestamp : {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Status    : {state.get('status', 'unknown')}")
        lines.append("")

        # ── Informazioni utente ──
        lines.append(sub_sep)
        lines.append("INFORMAZIONI UTENTE")
        lines.append(sub_sep)
        user_status = state.get("user_status", "ospite")
        lines.append(f"Tipo utente   : {user_status}")
        if user_status == "loggato":
            lines.append(f"Nome          : {state.get('user_name', 'N/A')} {state.get('user_surname', 'N/A')}")
            lines.append(f"Matricola     : {state.get('user_matricola', 'N/A')}")
            lines.append(f"Dipartimento  : {state.get('user_department', 'N/A')}")
            lines.append(f"Corso         : {state.get('user_course', 'N/A')}")
            lines.append(f"Tipologia     : {state.get('user_tipology', 'N/A')}")
            lines.append(f"Anno          : {state.get('user_year', 'N/A')}")
        else:
            lines.append("(Utente ospite - nessuna informazione di profilo disponibile)")
        lines.append("")

        # ── Query originale ──
        lines.append(sub_sep)
        lines.append("QUERY ORIGINALE DELL'UTENTE")
        lines.append(sub_sep)
        lines.append(state.get("query", "N/A"))
        lines.append("")

        # ── Storico conversazione ──
        conv = state.get("conversation_history")
        if conv:
            lines.append(sub_sep)
            lines.append("STORICO CONVERSAZIONE (recente)")
            lines.append(sub_sep)
            for msg in conv[-6:]:
                role = "Utente" if msg.get("role") == "user" else "Assistente"
                lines.append(f"[{role}]: {msg.get('content', '')[:300]}")
            lines.append("")

        # ── Elaborazione di ogni step della pipeline ──
        step_map = {s["step"]: s for s in workflow_steps}

        # 1. CLASSIFIER
        lines.extend(self._format_agent_section(
            "STEP 1 - CLASSIFIER AGENT",
            step_map.get("classification", {}),
            extra_fields=["category", "description", "confidence"]
        ))

        # 2. QUERY AGENT
        lines.extend(self._format_agent_section(
            "STEP 2 - QUERY AGENT",
            step_map.get("query_generation", {}),
            extra_fields=["search_query", "original_query"]
        ))

        # 3. WEB AGENT o EXAM EXTRACT (mutuamente esclusivi)
        if "exam_extract" in step_map:
            lines.extend(self._format_exam_extract_section(
                step_map.get("exam_extract", {})
            ))
        else:
            lines.extend(self._format_web_agent_section(
                step_map.get("web_search", {}),
                state.get("web_results", [])
            ))

        # 4. GENERATOR AGENT
        lines.extend(self._format_agent_section(
            "STEP 4 - GENERATOR AGENT",
            step_map.get("generation", {}),
            extra_fields=["category_used"],
            response_field="response"
        ))

        # 5. REVISION AGENT
        lines.extend(self._format_agent_section(
            "STEP 5 - REVISION AGENT",
            step_map.get("revision", {}),
            extra_fields=["has_changes"],
            response_field="revised_response"
        ))

        # ── Risposta finale ──
        lines.append(sep)
        lines.append("RISPOSTA FINALE")
        lines.append(sep)
        lines.append(state.get("final_response", "N/A"))
        lines.append("")

        # ── Errori ──
        error = state.get("error")
        if error:
            lines.append(sub_sep)
            lines.append("ERRORI")
            lines.append(sub_sep)
            lines.append(error)
            lines.append("")

        # ── Tempi di esecuzione ──
        lines.extend(self._format_timing_section(workflow_steps, total_time))

        lines.append(sep)
        lines.append("FINE DEL LOG")
        lines.append(sep)

        return lines

    def _format_agent_section(
        self,
        title: str,
        step_data: Dict,
        extra_fields: List[str] = None,
        response_field: str = "raw_response"
    ) -> List[str]:
        """
        Formatta una sezione standard dell'agente con system prompt, user prompt e risposta.
        """
        sep = "-" * 60
        lines = []
        lines.append(sep)
        lines.append(title)
        lines.append(sep)

        result = step_data.get("result", {})
        status = result.get("status", step_data.get("status", "N/A"))
        lines.append(f"Status: {status}")

        # Campi aggiuntivi (categoria, confidence, ecc.)
        if extra_fields:
            for field in extra_fields:
                value = result.get(field, "N/A")
                label = field.replace("_", " ").title()
                lines.append(f"{label}: {value}")
        lines.append("")

        # System prompt
        sys_prompt = result.get("system_prompt", "")
        if sys_prompt:
            lines.append(">>> SYSTEM PROMPT:")
            lines.append(sys_prompt)
            lines.append("")

        # User prompt
        user_prompt = result.get("user_prompt", "")
        if user_prompt:
            lines.append(">>> USER PROMPT:")
            lines.append(user_prompt)
            lines.append("")

        # Risposta
        raw_resp = result.get(response_field, "")
        if raw_resp:
            lines.append(">>> RISPOSTA:")
            lines.append(str(raw_resp))
            lines.append("")

        return lines

    def _format_web_agent_section(self, step_data: Dict, web_results: List[Dict]) -> List[str]:
        """
        Formatta la sezione del WebAgent mostrando la query di ricerca e i principali risultati.
        """
        sep = "-" * 60
        lines = []
        lines.append(sep)
        lines.append("STEP 3 - WEB AGENT (Tavily Search)")
        lines.append(sep)

        result = step_data.get("result", {})
        lines.append(f"Status              : {result.get('status', 'N/A')}")
        lines.append(f"Query di ricerca    : {result.get('search_query', 'N/A')}")
        lines.append(f"Totale risultati    : {result.get('total_results', 0)}")
        lines.append(f"Risultati usati     : {result.get('top_results_count', 0)}")
        lines.append("")

        if web_results:
            lines.append(">>> RISULTATI PRINCIPALI:")
            for r in web_results:
                lines.append(f"  [{r.get('rank', '?')}] Score: {r.get('score', 0):.4f}")
                lines.append(f"      Titolo   : {r.get('title', 'N/A')}")
                lines.append(f"      URL      : {r.get('url', 'N/A')}")
                content = r.get('content', '')
                lines.append(f"      Contenuto: {content}")
                lines.append("")
        else:
            lines.append(">>> Nessun risultato web recuperato.")
            lines.append("")

        return lines

    def _format_exam_extract_section(self, step_data: Dict) -> List[str]:
        """
        Formatta la sezione dell'Exam Extract mostrando la selezione del link,
        il contenuto estratto e le fonti web aggiuntive.
        """
        sep = "-" * 60
        lines = []
        lines.append(sep)
        lines.append("STEP 3 - WEB AGENT (Exam Calendar Extract)")
        lines.append(sep)

        result = step_data.get("result", {})
        lines.append(f"Status              : {result.get('status', 'N/A')}")
        lines.append(f"Query di ricerca    : {result.get('search_query', 'N/A')}")
        lines.append("")

        # Selezione link
        lines.append(">>> SELEZIONE CALENDARIO:")
        lines.append(f"  Polo/Dipartimento : {result.get('selected_polo', 'N/A')}")
        lines.append(f"  Sessione          : {result.get('selected_sessione', 'N/A')}")
        lines.append(f"  URL selezionato   : {result.get('selected_url', 'N/A')}")
        lines.append(f"  Motivazione       : {result.get('selection_reasoning', 'N/A')}")
        lines.append("")

        # LLM prompt e risposta per la selezione
        sel_prompt = result.get("selection_llm_prompt", "")
        if sel_prompt:
            lines.append(">>> PROMPT SELEZIONE LINK:")
            lines.append(sel_prompt)
            lines.append("")

        sel_response = result.get("selection_llm_response", "")
        if sel_response:
            lines.append(">>> RISPOSTA LLM SELEZIONE:")
            lines.append(sel_response)
            lines.append("")

        # Extract
        lines.append(">>> TAVILY EXTRACT:")
        lines.append(f"  URL estratto      : {result.get('extract_url', 'N/A')}")
        lines.append(f"  Status extract    : {result.get('extract_status', 'N/A')}")
        lines.append(f"  Lunghezza content : {result.get('extract_content_length', 0)} caratteri")
        lines.append("")

        extract_content = result.get("extract_content", "")
        if extract_content:
            lines.append(">>> CONTENUTO ESTRATTO DAL CALENDARIO:")
            lines.append(extract_content)
            lines.append("")

        # Fonti web aggiuntive
        web_count = result.get("web_results_count", 0)
        lines.append(f"  Fonti web aggiuntive: {web_count}")
        lines.append("")

        return lines

    def _format_timing_section(self, workflow_steps: List[Dict], total_time: float = None) -> List[str]:
        """
        Formatta la sezione riepilogativa dei tempi di esecuzione di ogni agente e il tempo totale.
        """
        sep = "=" * 80
        sub_sep = "-" * 60
        lines = []

        lines.append(sub_sep)
        lines.append("TEMPI DI ESECUZIONE")
        lines.append(sub_sep)

        # Mappa nomi leggibili per ogni step
        step_labels = {
            "classification": "Classifier Agent",
            "query_generation": "Query Agent",
            "web_search": "Web Agent",
            "exam_extract": "Web Agent (Exam Extract)",
            "generation": "Generator Agent",
            "revision": "Revision Agent",
        }

        for step in workflow_steps:
            step_name = step.get("step", "sconosciuto")
            label = step_labels.get(step_name, step_name)
            elapsed = step.get("elapsed_time")
            if elapsed is not None:
                lines.append(f"  {label:<25}: {elapsed:.3f}s")
            else:
                lines.append(f"  {label:<25}: N/A")

        lines.append("")

        if total_time is not None:
            lines.append(f"  {'TEMPO TOTALE':<25}: {total_time:.3f}s")
        else:
            lines.append(f"  {'TEMPO TOTALE':<25}: N/A")

        lines.append("")

        return lines
