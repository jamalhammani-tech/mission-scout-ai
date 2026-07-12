"""Analyse IA du texte d'un CV -> `CvExtraction` structurée (appel Anthropic en tool use)."""

from functools import lru_cache
from typing import Protocol

import anthropic

from cv_agent.schemas import CvExtraction
from cv_agent.settings import REPO_ROOT

_PROMPT_PATH = REPO_ROOT / "prompts" / "cv-agent" / "extraction-cv.md"
_TOOL_NAME = "extraire_cv"


class LlmExtractor(Protocol):
    def extraire(self, texte_cv: str) -> CvExtraction: ...


@lru_cache
def _charger_prompt() -> str:
    return _PROMPT_PATH.read_text(encoding="utf-8")


def _schema_outil() -> dict[str, object]:
    schema = CvExtraction.model_json_schema()
    return {
        "name": _TOOL_NAME,
        "description": "Enregistre les informations structurées extraites d'un CV.",
        "input_schema": schema,
    }


class AnthropicLlmExtractor:
    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model

    def extraire(self, texte_cv: str) -> CvExtraction:
        # Le SDK Anthropic type `tools`/`tool_choice` avec des TypedDict précis ;
        # un schéma JSON généré dynamiquement (Pydantic) ne peut pas être vérifié
        # statiquement contre ces types — ignoré volontairement à cette frontière.
        response = self._client.messages.create(  # type: ignore[call-overload]
            model=self._model,
            max_tokens=4096,
            system=_charger_prompt(),
            tools=[_schema_outil()],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": texte_cv}],
        )

        for bloc in response.content:
            if bloc.type == "tool_use" and bloc.name == _TOOL_NAME:
                return CvExtraction.model_validate(bloc.input)

        raise RuntimeError("La réponse Anthropic ne contient pas l'appel d'outil attendu.")
