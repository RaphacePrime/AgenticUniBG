import os
from datetime import datetime
from typing import Dict, List, Optional


class PipelineLogger:
    """
    Logger that creates a detailed log file for each user query,
    capturing the full pipeline: Classifier → QueryAgent → WebAgent → Generator → Reviser.
    """

    LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")

    def __init__(self):
        os.makedirs(self.LOGS_DIR, exist_ok=True)

    def _build_filename(self, matricola: Optional[str], timestamp: datetime) -> str:
        """
        Build the log filename: log_{matricola}_{timestamp} or log_ospite_{timestamp}
        """
        user_id = matricola if matricola else "ospite"
        ts = timestamp.strftime("%Y%m%d_%H%M%S_%f")
        return f"log_{user_id}_{ts}.txt"

    def write_log(self, state: Dict, workflow_steps: List[Dict], timestamp: datetime = None) -> str:
        """
        Write a full pipeline log file and return the file path.
        """
        if timestamp is None:
            timestamp = datetime.now()

        matricola = state.get("user_matricola")
        filename = self._build_filename(matricola, timestamp)
        filepath = os.path.join(self.LOGS_DIR, filename)

        lines = self._build_log_content(state, workflow_steps, timestamp)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return filepath

    def _build_log_content(self, state: Dict, workflow_steps: List[Dict], timestamp: datetime) -> List[str]:
        """
        Build the full log content as a list of lines.
        """
        sep = "=" * 80
        sub_sep = "-" * 60
        lines = []

        # ── Header ──
        lines.append(sep)
        lines.append("AGENTIC UNIBG - PIPELINE LOG")
        lines.append(sep)
        lines.append(f"Timestamp : {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Status    : {state.get('status', 'unknown')}")
        lines.append("")

        # ── User Info ──
        lines.append(sub_sep)
        lines.append("USER INFORMATION")
        lines.append(sub_sep)
        user_status = state.get("user_status", "ospite")
        lines.append(f"User type   : {user_status}")
        if user_status == "loggato":
            lines.append(f"Name        : {state.get('user_name', 'N/A')} {state.get('user_surname', 'N/A')}")
            lines.append(f"Matricola   : {state.get('user_matricola', 'N/A')}")
            lines.append(f"Department  : {state.get('user_department', 'N/A')}")
            lines.append(f"Course      : {state.get('user_course', 'N/A')}")
            lines.append(f"Typology    : {state.get('user_tipology', 'N/A')}")
            lines.append(f"Year        : {state.get('user_year', 'N/A')}")
        else:
            lines.append("(Guest user - no profile information available)")
        lines.append("")

        # ── Original Query ──
        lines.append(sub_sep)
        lines.append("ORIGINAL USER QUERY")
        lines.append(sub_sep)
        lines.append(state.get("query", "N/A"))
        lines.append("")

        # ── Conversation History ──
        conv = state.get("conversation_history")
        if conv:
            lines.append(sub_sep)
            lines.append("CONVERSATION HISTORY (recent)")
            lines.append(sub_sep)
            for msg in conv[-6:]:
                role = "User" if msg.get("role") == "user" else "Assistant"
                lines.append(f"[{role}]: {msg.get('content', '')[:300]}")
            lines.append("")

        # ── Process each pipeline step ──
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

        # 3. WEB AGENT
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

        # ── Final Response ──
        lines.append(sep)
        lines.append("FINAL RESPONSE")
        lines.append(sep)
        lines.append(state.get("final_response", "N/A"))
        lines.append("")

        # ── Errors ──
        error = state.get("error")
        if error:
            lines.append(sub_sep)
            lines.append("ERRORS")
            lines.append(sub_sep)
            lines.append(error)
            lines.append("")

        lines.append(sep)
        lines.append("END OF LOG")
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
        Format a standard agent section with system prompt, user prompt, and response.
        """
        sep = "-" * 60
        lines = []
        lines.append(sep)
        lines.append(title)
        lines.append(sep)

        result = step_data.get("result", {})
        status = result.get("status", step_data.get("status", "N/A"))
        lines.append(f"Status: {status}")

        # Extra fields (category, confidence, etc.)
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

        # Response
        raw_resp = result.get(response_field, "")
        if raw_resp:
            lines.append(">>> RESPONSE:")
            lines.append(str(raw_resp))
            lines.append("")

        return lines

    def _format_web_agent_section(self, step_data: Dict, web_results: List[Dict]) -> List[str]:
        """
        Format the WebAgent section showing search query and top results.
        """
        sep = "-" * 60
        lines = []
        lines.append(sep)
        lines.append("STEP 3 - WEB AGENT (Tavily Search)")
        lines.append(sep)

        result = step_data.get("result", {})
        lines.append(f"Status          : {result.get('status', 'N/A')}")
        lines.append(f"Search query    : {result.get('search_query', 'N/A')}")
        lines.append(f"Total results   : {result.get('total_results', 0)}")
        lines.append(f"Top results used: {result.get('top_results_count', 0)}")
        lines.append("")

        if web_results:
            lines.append(">>> TOP RESULTS:")
            for r in web_results:
                lines.append(f"  [{r.get('rank', '?')}] Score: {r.get('score', 0):.4f}")
                lines.append(f"      Title  : {r.get('title', 'N/A')}")
                lines.append(f"      URL    : {r.get('url', 'N/A')}")
                content = r.get('content', '')
                lines.append(f"      Content: {content}")
                lines.append("")
        else:
            lines.append(">>> No web results retrieved.")
            lines.append("")

        return lines
