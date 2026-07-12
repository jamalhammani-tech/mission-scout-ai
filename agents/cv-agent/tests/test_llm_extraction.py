import pytest
from pydantic import ValidationError

from cv_agent.llm_extraction import _valider_extraction


def test_valider_extraction_champs_a_plat() -> None:
    extraction = _valider_extraction(
        {"resume_professionnel": "Résumé.", "nom": "Jean Dupont", "titre": "Développeur"}
    )
    assert extraction.nom == "Jean Dupont"


def test_valider_extraction_reponse_imbriquee_sous_une_cle_wrapper() -> None:
    # Observé en usage réel sur des CV longs : le modèle imbrique parfois sa réponse.
    extraction = _valider_extraction(
        {"cv_extraction": {"resume_professionnel": "Résumé.", "nom": "Jean Dupont"}}
    )
    assert extraction.nom == "Jean Dupont"
    assert extraction.resume_professionnel == "Résumé."


def test_valider_extraction_erreur_non_recuperable_leve_validation_error() -> None:
    with pytest.raises(ValidationError):
        _valider_extraction({"cv_extraction": "pas un dict"})
