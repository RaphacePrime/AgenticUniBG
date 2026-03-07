from typing import Dict, List, Optional
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
import datetime
import requests
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# ─── Mesi in italiano ─────────────────────────────────────────────
MESI_ITALIANI = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"
]

def get_italian_timestamp() -> str:
    """Restituisce la data corrente in formato italiano, es. '04 marzo 2026'."""
    now = datetime.datetime.now()
    return f"{now.day:02d} {MESI_ITALIANI[now.month - 1]} {now.year}"

# ─── Calendari esami per dipartimento / polo ──────────────────────
EXAM_CALENDAR_LINKS = {
    "Scuola di Ingegneria": [
        {"sessione": "invernale", "url": None, "note": "Già conclusa"},
        {"sessione": "intermedia/aprile straordinaria", "url": "https://www.unibg.it/sites/default/files/media/documents/2026-02-09/appelli25-26_aprile.pdf"},
        {"sessione": "estiva", "url": "https://www.unibg.it/sites/default/files/media/documents/2026-02-23/estiva%202026.pdf"},
        {"sessione": "autunnale", "url": "https://www.unibg.it/sites/default/files/media/documents/2026-02-23/autunno%2026.pdf"},
    ],
    "Polo Economico-Giuridico": [
        {"sessione": "invernale", "url": None, "note": "Non disponibile"},
        {"sessione": "intermedia/aprile straordinaria", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Economico-Giuridico/628/ttTotalHtml.html"},
        {"sessione": "estiva", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Economico-Giuridico/606/ttPdf.pdf"},
        {"sessione": "autunnale", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Economico-Giuridico/607/ttPdf.pdf"},
    ],
    "Polo Linguistico": [
        {"sessione": "invernale", "url": None, "note": "Già conclusa"},
        {"sessione": "intermedia/aprile straordinaria", "url": None, "note": "Non ancora disponibile"},
        {"sessione": "estiva", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_di_Lingue_e_culture_straniere/614/ttPdf.pdf"},
        {"sessione": "autunnale", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_di_Lingue_e_culture_straniere/615/ttPdf.pdf"},
    ],
    "Polo Umanistico": [
        {"sessione": "invernale", "url": None, "note": "Non disponibile"},
        {"sessione": "intermedia/primaverile", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Umanistico/617/ttPdf.pdf"},
        {"sessione": "scienze formazione primaria/fine maggio", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Umanistico/618/ttPdf.pdf"},
        {"sessione": "estiva", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Umanistico/619/ttPdf.pdf"},
        {"sessione": "autunnale", "url": "https://logistica.unibg.it/Esami/Calendario/Polo_Umanistico/620/ttPdf.pdf"},
    ],
}

EXAM_PORTAL_LINK = "https://logistica.unibg.it/PortaleStudenti/index.php?view=easytest&_lang=it"


class WebAgent:
    """
    Agente che esegue ricerche web tramite Tavily API
    su domini specifici dell'Università di Bergamo e restituisce
    i risultati testuali più rilevanti.
    """

    # Domini su cui cercare
    SEARCH_DOMAINS = [
        "unibg.it",
        "unibg.coursecatalogue.cineca.it"
    ]

    def __init__(self, llm: ChatGoogleGenerativeAI = None):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY non configurata nelle variabili d'ambiente")
        self.client = TavilyClient(api_key=api_key)
        self.llm = llm

    def _is_pdf_url(self, url: str) -> bool:
        """
        Controlla se l'URL punta a un PDF.
        """
        return url.lower().split("?")[0].endswith(".pdf")

    def _extract_pdf_links(self, pdf_url: str) -> List[Dict]:
        """
        Scarica il PDF in memoria ed estrae tutti i link ipertestuali.
        Restituisce una lista di {uri, page}.
        """
        if not PYMUPDF_AVAILABLE:
            return []
        try:
            response = requests.get(pdf_url, timeout=10)
            response.raise_for_status()
            doc = fitz.open(stream=response.content, filetype="pdf")
            links = []
            seen = set()
            for page_num, page in enumerate(doc, 1):
                for link in page.get_links():
                    uri = link.get("uri", "")
                    if uri and uri not in seen:
                        seen.add(uri)
                        links.append({"uri": uri, "page": page_num})
            return links
        except Exception:
            return []

    async def search(self, search_query: str) -> Dict:
        """
        Esegue una ricerca web con Tavily sulla query fornita,
        recupera 30 risultati e restituisce i top 5 per score.
        """
        try:
            response = self.client.search(
                query=search_query,
                search_depth="advanced",
                include_domains=self.SEARCH_DOMAINS,
                max_results=30,
                chunks_per_source=5,
                include_raw_content=True
            )

            results = response.get("results", [])

            # Ordina per score decrescente e prendi i top 5
            sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
            top_results = sorted_results[:5]

            # Estrai le informazioni testuali rilevanti
            web_contents = []
            for i, result in enumerate(top_results, 1):
                url = result.get("url", "")
                pdf_links = []
                if self._is_pdf_url(url):
                    pdf_links = self._extract_pdf_links(url)

                web_contents.append({
                    "rank": i,
                    "title": result.get("title", ""),
                    "url": url,
                    "content": result.get("raw_content", "") or result.get("content", ""),
                    "score": result.get("score", 0),
                    "is_pdf": self._is_pdf_url(url),
                    "pdf_links": pdf_links
                })

            # Costruisci il testo formattato da passare al generator
            formatted_text = self._format_results(web_contents)

            return {
                "web_results": web_contents,
                "formatted_context": formatted_text,
                "search_query": search_query,
                "total_results": len(results),
                "top_results_count": len(top_results),
                "status": "success"
            }

        except Exception as e:
            return {
                "web_results": [],
                "formatted_context": "",
                "search_query": search_query,
                "total_results": 0,
                "top_results_count": 0,
                "status": "error",
                "error": str(e)
            }

    def _format_results(self, results: List[Dict]) -> str:
        """
        Formatta i risultati web in un testo leggibile da passare al generator.
        """
        if not results:
            return "Nessun risultato trovato dalla ricerca web."

        lines = ["INFORMAZIONI DAL SITO DELL'UNIVERSITÀ DI BERGAMO:"]
        lines.append("")

        for result in results:
            lines.append(f"Fonte {result['rank']}: {result['title']}")
            lines.append(f"URL: {result['url']}")
            if result.get("is_pdf") and result.get("pdf_links"):
                lines.append("Tipo: PDF")
                lines.append("Link estratti dal PDF:")
                for lnk in result["pdf_links"]:
                    lines.append(f"  - {lnk['uri']} (pagina {lnk['page']})")
            lines.append(f"Contenuto: {result['content']}")
            lines.append("")

        return "\n".join(lines)

    # ─── Metodi per la categoria date_esami ───────────────────────

    def _get_all_calendars(self) -> Dict:
        """
        Restituisce TUTTI i calendari disponibili.
        La scelta del polo/dipartimento corretto viene delegata all'LLM
        che decide in base al contenuto della query dell'utente
        (non in base al dipartimento del profilo utente).
        """
        return EXAM_CALENDAR_LINKS

    async def _select_calendar_link(self, query: str, calendars: Dict, user_context: str = "") -> Dict:
        """
        Usa l'LLM per scegliere quale link del calendario estrarre
        in base alla domanda dell'utente e al periodo attuale.
        Restituisce un dict con: polo, sessione, url, reasoning.
        """
        today = get_italian_timestamp()

        # Costruisci la lista dei link disponibili
        options_lines = []
        option_idx = 1
        option_map = {}
        for polo, sessions in calendars.items():
            for s in sessions:
                if s.get("url"):
                    label = f"{option_idx}. {polo} - sessione {s['sessione']} → {s['url']}"
                    options_lines.append(label)
                    option_map[str(option_idx)] = {"polo": polo, "sessione": s["sessione"], "url": s["url"]}
                    option_idx += 1
                else:
                    note = s.get("note", "Non disponibile")
                    options_lines.append(f"(non disponibile) {polo} - sessione {s['sessione']}: {note}")

        if not option_map:
            return {"polo": None, "sessione": None, "url": None, "reasoning": "Nessun link disponibile"}

        options_text = "\n".join(options_lines)

        prompt = f"""Oggi è il {today}. Anno accademico 2025/2026.

L'utente ha chiesto: "{query}"

{user_context}

Ecco i link ai calendari esami disponibili:
0. NON È POSSIBILE DETERMINARE IL CALENDARIO — L'utente non ha specificato un corso o dipartimento e non è autenticato. Non scegliere un calendario a caso.
{options_text}

Portale generale esami: {EXAM_PORTAL_LINK}

Scegli IL NUMERO del link più appropriato da cui estrarre le date degli esami per rispondere alla domanda dell'utente.

REGOLA CRITICA:
- Se l'utente è un OSPITE (non autenticato) E la sua domanda NON specifica un corso, dipartimento o polo preciso (es. "che esami ho?", "esami quest'anno?", "prossima sessione?"), DEVI rispondere con NUMERO: 0.
  In questo caso NON scegliere un calendario a caso (es. Ingegneria). Senza sapere il corso dell'utente, non puoi sapere quale calendario serve.
- Rispondi con un numero diverso da 0 SOLO se:
  a) L'utente è autenticato (ha un profilo con corso/dipartimento), OPPURE
  b) L'utente ha specificato esplicitamente nella domanda il corso, il dipartimento o il polo (es. "esami di giurisprudenza", "calendario ingegneria", "esami polo umanistico").

IMPORTANTE: Scegli il calendario del POLO/DIPARTIMENTO che corrisponde alla domanda dell'utente, NON necessariamente quello del suo profilo.
Per esempio, se l'utente è iscritto a Ingegneria ma chiede degli esami di Giurisprudenza, scegli il calendario del Polo Economico-Giuridico.
Considera quale sessione è più vicina o pertinente alla domanda.
Se la domanda dice "prossima sessione", scegli la sessione più prossima tra quelle disponibili rispetto alla data odierna.

Rispondi con questo formato esatto:
NUMERO: <numero>
MOTIVO: <breve spiegazione>"""

        try:
            messages = [
                SystemMessage(content="Sei un assistente che aiuta a scegliere il calendario esami corretto per l'Università di Bergamo. Rispondi SOLO nel formato richiesto."),
                HumanMessage(content=prompt)
            ]
            response = await self.llm.ainvoke(messages)
            text = response.content.strip()

            # Parsing del numero
            chosen = None
            reasoning = text
            for line in text.split("\n"):
                if line.strip().upper().startswith("NUMERO:"):
                    num = line.split(":", 1)[1].strip().split()[0]
                    if num == "0":
                        # L'LLM ha scelto 0: non è possibile determinare il calendario
                        chosen = {"polo": None, "sessione": None, "url": None}
                        break
                    if num in option_map:
                        chosen = option_map[num]
                        break
                if line.strip().upper().startswith("MOTIVO:"):
                    reasoning = line.split(":", 1)[1].strip()

            if chosen is not None:
                chosen["reasoning"] = reasoning
                chosen["llm_response"] = text
                chosen["prompt"] = prompt
                return chosen
            else:
                # Fallback: primo link disponibile
                first = list(option_map.values())[0]
                first["reasoning"] = "Fallback: nessuna scelta chiara dall'LLM"
                first["llm_response"] = text
                first["prompt"] = prompt
                return first

        except Exception as e:
            first = list(option_map.values())[0]
            first["reasoning"] = f"Errore LLM, fallback al primo link: {str(e)}"
            first["prompt"] = prompt
            return first

    async def extract(self, url: str) -> Dict:
        """
        Usa Tavily .extract() per estrarre il contenuto completo di una URL.
        """
        try:
            response = self.client.extract(urls=[url])

            results = response.get("results", [])
            if results:
                content = results[0].get("raw_content", "") or results[0].get("text", "")
                return {
                    "url": url,
                    "content": content,
                    "status": "success"
                }
            else:
                return {
                    "url": url,
                    "content": "",
                    "status": "no_content"
                }
        except Exception as e:
            return {
                "url": url,
                "content": "",
                "status": "error",
                "error": str(e)
            }

    async def search_and_extract_exams(self, query: str, user_department: Optional[str] = None, user_context: str = "") -> Dict:
        """
        Flusso completo per la categoria date_esami:
        1. Determina i calendari per il dipartimento
        2. LLM sceglie il link giusto
        3. Tavily extract sul link scelto
        4. Tavily search per le top 3 fonti generiche
        5. Restituisce tutto al generator
        """
        # 1. Tutti i calendari disponibili (l'LLM sceglie il polo in base alla query)
        calendars = self._get_all_calendars()

        # 2. LLM sceglie il link
        link_selection = await self._select_calendar_link(query, calendars, user_context)
        chosen_url = link_selection.get("url")

        # 3. Extract del calendario scelto
        extract_result = {}
        if chosen_url:
            extract_result = await self.extract(chosen_url)

        # 4. Search generica per contesto aggiuntivo (top 3)
        search_result = await self.search(query)
        top3_web = []
        if search_result.get("web_results"):
            top3_web = search_result["web_results"][:3]

        # 5. Formatta tutto
        formatted = self._format_exam_results(link_selection, extract_result, top3_web)

        return {
            "link_selection": link_selection,
            "extract_result": extract_result,
            "web_results": top3_web,
            "formatted_context": formatted,
            "search_query": query,
            "status": "success"
        }

    def _format_exam_results(self, link_selection: Dict, extract_result: Dict, web_results: List[Dict]) -> str:
        """
        Formatta i risultati per date_esami da passare al generator.
        """
        today = get_italian_timestamp()
        lines = [f"DATA ODIERNA: {today}", ""]

        # Caso: nessun calendario selezionato (ospite senza corso specificato)
        if link_selection.get("polo") is None and link_selection.get("url") is None:
            lines.append("═══ CALENDARIO ESAMI ═══")
            lines.append("Non è stato possibile determinare quale calendario consultare.")
            lines.append("L'utente non ha specificato il corso o il dipartimento e non è autenticato.")
            lines.append("Chiedi gentilmente all'utente quale corso di laurea o dipartimento frequenta per poter consultare il calendario corretto.")
            lines.append(f"Motivo: {link_selection.get('reasoning', 'N/D')}")
            lines.append("")
        # Calendario estratto con successo
        elif extract_result.get("content"):
            lines.append("═══ CALENDARIO ESAMI ESTRATTO ═══")
            lines.append(f"Polo/Dipartimento: {link_selection.get('polo', 'N/D')}")
            lines.append(f"Sessione: {link_selection.get('sessione', 'N/D')}")
            lines.append(f"URL: {extract_result.get('url', 'N/D')}")
            lines.append(f"Motivo della scelta: {link_selection.get('reasoning', 'N/D')}")
            lines.append("")
            lines.append("Contenuto del calendario:")
            lines.append(extract_result["content"])
            lines.append("")
        else:
            lines.append("═══ CALENDARIO ESAMI ═══")
            lines.append("Non è stato possibile estrarre il calendario.")
            if link_selection.get("url"):
                lines.append(f"Link del calendario: {link_selection['url']}")
            lines.append(f"Motivo: {link_selection.get('reasoning', 'N/D')}")
            lines.append("")

        # Portale generale
        lines.append(f"Portale generale esami UniBG: {EXAM_PORTAL_LINK}")
        lines.append("")

        # Risultati web aggiuntivi
        if web_results:
            lines.append("═══ FONTI WEB AGGIUNTIVE ═══")
            for r in web_results:
                lines.append(f"Fonte {r.get('rank', '?')}: {r.get('title', 'N/D')}")
                lines.append(f"URL: {r.get('url', 'N/D')}")
                lines.append(f"Contenuto: {r.get('content', '')}")
                lines.append("")

        return "\n".join(lines)
