"""Récupération du texte d'une annonce : soit collé directement, soit une seule requête HTTP
ciblée vers une URL fournie explicitement par l'utilisateur.

Ce n'est pas du scraping automatisé : une requête ponctuelle, à la demande, avec un
User-Agent transparent (pas d'imitation de navigateur), sans contournement de protection
ni comportement de crawl. Si le site bloque ou nécessite une connexion, l'échec est
signalé clairement — pas de contournement, l'utilisateur colle le texte à la place.
"""

import httpx
from bs4 import BeautifulSoup

_USER_AGENT = "mission-scout-ai-career-scout-agent/0.1 (usage personnel, recherche de mission)"
_TIMEOUT_SECONDES = 15.0


def recuperer_texte_url(url: str) -> str:
    try:
        reponse = httpx.get(
            url, headers={"User-Agent": _USER_AGENT}, timeout=_TIMEOUT_SECONDES, follow_redirects=True
        )
        reponse.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(
            f"Impossible de récupérer l'URL ({exc}). Réessaie avec --texte en collant l'annonce directement."
        ) from exc

    texte = _html_vers_texte(reponse.text)
    if not texte:
        raise ValueError(f"Aucun texte exploitable extrait de {url}. Réessaie avec --texte.")
    return texte


def _html_vers_texte(html: str) -> str:
    soupe = BeautifulSoup(html, "html.parser")
    for balise in soupe(["script", "style", "nav", "footer", "header"]):
        balise.decompose()

    lignes = (ligne.strip() for ligne in soupe.get_text(separator="\n").splitlines())
    return "\n".join(ligne for ligne in lignes if ligne)
