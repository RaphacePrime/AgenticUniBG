from typing import Dict, List, Optional
from tavily import TavilyClient
import os


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

    def __init__(self):
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise ValueError("TAVILY_API_KEY non configurata nelle variabili d'ambiente")
        self.client = TavilyClient(api_key=api_key)

    async def search(self, search_query: str) -> Dict:
        """
        Esegue una ricerca web con Tavily sulla query fornita,
        recupera 10 risultati e restituisce i top 5 per score.
        """
        try:
            # Esegui la ricerca Tavily (sincrona, wrappata)
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
                web_contents.append({
                    "rank": i,
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("raw_content", "") or result.get("content", ""),
                    "score": result.get("score", 0)
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
            lines.append(f"Contenuto: {result['content']}")
            lines.append("")

        return "\n".join(lines)
