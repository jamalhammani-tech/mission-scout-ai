"""Point d'entrée `uv run import-cv mon_cv.pdf`."""

import argparse
import sys
from pathlib import Path

import anthropic
from memory_agent.db import session_scope
from memory_agent.logging_config import configure_logging
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from cv_agent.import_cv import ResultatImportCv, importer_cv
from cv_agent.llm_extraction import AnthropicLlmExtractor
from cv_agent.settings import get_settings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="import-cv", description="Importe un CV (PDF ou DOCX) dans le Memory Agent."
    )
    parser.add_argument("fichier", type=Path, help="Chemin du CV à importer (.pdf ou .docx)")
    parser.add_argument("--email", help="Email du propriétaire du profil (sinon CV_AGENT_USER_EMAIL)")
    parser.add_argument("--nom", help="Nom à utiliser si un nouvel utilisateur doit être créé")
    return parser.parse_args(argv)


def _afficher_resultat(resultat: ResultatImportCv) -> None:
    e = resultat.extraction
    print()
    print("=" * 60)
    print("Import terminé")
    print("=" * 60)
    print(f"Utilisateur     : {resultat.user.email}")
    print(f"Profil          : {'mis à jour' if resultat.profil_deja_existant else 'créé'}")
    print(f"Titre           : {resultat.profil.titre or '(non détecté)'}")
    print(f"Expériences     : {len(resultat.profil.experiences)}")
    print(f"Compétences     : {len(resultat.profil.competences)}")
    print(f"Certifications  : {len(e.certifications)} (non persistées — MVP)")
    print(f"Langues         : {', '.join(e.langues) or '(non détectées)'}")
    print(f"Secteurs        : {', '.join(e.secteurs) or '(non détectés)'}")
    print(f"Document CV     : {resultat.document.reference_fichier}")
    print()
    print("Résumé professionnel :")
    print(e.resume_professionnel)
    print("=" * 60)


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = _parse_args(argv)

    if not args.fichier.exists():
        print(f"Erreur : fichier introuvable : {args.fichier}", file=sys.stderr)
        sys.exit(1)

    try:
        settings = get_settings()
    except ValidationError:
        print(
            "Erreur : ANTHROPIC_API_KEY n'est pas configurée (config/.env ou variable d'environnement).",
            file=sys.stderr,
        )
        sys.exit(1)

    email = args.email or settings.cv_agent_user_email
    if not email:
        print(
            "Erreur : --email requis (ou variable d'environnement CV_AGENT_USER_EMAIL).",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    extracteur = AnthropicLlmExtractor(client, settings.anthropic_model)

    try:
        with session_scope() as session:
            resultat = importer_cv(
                args.fichier,
                email=email,
                nom_fallback=args.nom,
                extracteur=extracteur,
                session=session,
            )
    except ValueError as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        sys.exit(1)
    except OperationalError as exc:
        print(
            f"Erreur : impossible de se connecter à la base de données ({exc.orig}). "
            "PostgreSQL est-il démarré ? (docker compose up -d, ou service postgresql start)",
            file=sys.stderr,
        )
        sys.exit(1)
    except anthropic.APIError as exc:
        print(f"Erreur : l'appel à l'API Anthropic a échoué ({exc}).", file=sys.stderr)
        sys.exit(1)

    _afficher_resultat(resultat)


if __name__ == "__main__":
    main()
