"""Analyse IA du texte d'une annonce -> `AnalyseMission` structurée (appel Anthropic en tool use)."""

from functools import lru_cache
from typing import Protocol

import anthropic
from pydantic import ValidationError

from mission_agent.schemas import AnalyseMission
from mission_agent.settings import REPO_ROOT

_PROMPT_PATH = REPO_ROOT / "prompts" / "mission-agent" / "analyse-mission.md"
_TOOL_NAME = "analyser_mission"


class AnalyseurMission(Protocol):
    def analyser(self, texte_annonce: str) -> AnalyseMission: ...


@lru_cache
def _charger_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _schema_outil() -> dict[str, object]:
    schema = AnalyseMission.model_json_schema()
    return {
        "name": _TOOL_NAME,
        "description": "Enregistre les informations structurées extraites d'une annonce de mission.",
        "input_schema": schema,
    }


def _valider_analyse(donnees: dict[str, object]) -> AnalyseMission:
    """Valide `donnees` en `AnalyseMission`.

    Le modèle imbrique parfois sa réponse sous une unique clé wrapper (même comportement
    observé côté cv-agent sur des textes longs/complexes) au lieu de renvoyer les champs à
    plat comme demandé par le schéma. On retente alors sur cette valeur imbriquée.
    """
    try:
        return AnalyseMission.model_validate(donnees)
    except ValidationError:
        if len(donnees) == 1:
            (valeur_unique,) = donnees.values()
            if isinstance(valeur_unique, dict):
                return AnalyseMission.model_validate(valeur_unique)
        raise


class AnthropicAnalyseurMission:
    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def analyser(self, texte_annonce: str) -> AnalyseMission:
        # Le SDK Anthropic type `tools`/`tool_choice` avec des TypedDict précis ;
        # un schéma JSON généré dynamiquement (Pydantic) ne peut pas être vérifié
        # statiquement contre ces types — ignoré volontairement à cette frontière.
        response = self._client.messages.create(  # type: ignore[call-overload]
            model=self._model,
            max_tokens=4096,
            system=_charger_prompt(),
            tools=[_schema_outil()],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": texte_annonce}],
        )

        for bloc in response.content:
            if bloc.type == "tool_use" and bloc.name == _TOOL_NAME:
                return _valider_analyse(bloc.input)

        raise RuntimeError("La réponse Anthropic ne contient pas l'appel d'outil attendu.")
