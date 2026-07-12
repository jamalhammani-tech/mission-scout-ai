import pytest
from pydantic import ValidationError

from mission_agent.llm_analysis import _valider_analyse


def test_valider_analyse_champs_a_plat() -> None:
    analyse = _valider_analyse({"titre": "Développeur Python", "resume": "Résumé."})
    assert analyse.titre == "Développeur Python"


def test_valider_analyse_reponse_imbriquee_sous_une_cle_wrapper() -> None:
    # Observé côté cv-agent sur des textes longs/complexes : le modèle imbrique parfois sa réponse.
    analyse = _valider_analyse({"analyse_mission": {"titre": "Développeur Python", "resume": "Résumé."}})
    assert analyse.titre == "Développeur Python"
    assert analyse.resume == "Résumé."


def test_valider_analyse_erreur_non_recuperable_leve_validation_error() -> None:
    with pytest.raises(ValidationError):
        _valider_analyse({"analyse_mission": "pas un dict"})
