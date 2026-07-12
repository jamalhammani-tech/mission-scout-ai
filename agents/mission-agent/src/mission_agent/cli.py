"""Point d'entrée `uv run scout import-mission --url ... | --texte ...`."""

import argparse
import sys

import anthropic
from memory_agent.db import session_scope
from memory_agent.logging_config import configure_logging
from pydantic import ValidationError
from sqlalchemy.exc import OperationalError

from mission_agent.import_mission import ResultatImportMission, importer_mission
from mission_agent.llm_analysis import AnthropicAnalyseurMission
from mission_agent.settings import get_settings


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="scout", description="Career Scout Agent — recherche de missions IT."
    )
    sous_commandes = parser.add_subparsers(dest="commande", required=True)

    import_mission = sous_commandes.add_parser(
        "import-mission", help="Importe une mission, l'analyse et calcule son score de matching."
    )
    source = import_mission.add_mutually_exclusive_group(required=True)
    source.add_argument("--url", help="URL de l'annonce à récupérer")
    source.add_argument("--texte", help="Texte de l'annonce collé directement")
    import_mission.add_argument(
        "--email", help="Email du propriétaire du profil (sinon MISSION_AGENT_USER_EMAIL)"
    )

    return parser.parse_args(argv)


def _afficher_resultat(resultat: ResultatImportMission) -> None:
    a = resultat.analyse
    r = resultat.rapport
    tjm = resultat.mission.tjm

    print()
    print("=" * 60)
    print("Mission " + ("déjà connue" if resultat.mission_deja_connue else "importée"))
    print("=" * 60)
    print(f"Titre           : {a.titre}")
    print(f"Entreprise      : {a.entreprise or '(non détectée)'}")
    print(f"Lieu            : {a.lieu or '(non détecté)'}")
    print(f"Type de contrat : {a.type_contrat or '(non détecté)'}")
    if tjm.montant_min or tjm.montant_max:
        print(
            f"TJM             : {tjm.montant_min or '?'} - {tjm.montant_max or '?'} {tjm.devise}/{tjm.unite}"
        )
    else:
        print("TJM             : (non précisé)")
    print()
    print(f"Score           : {r.score_pourcent:.1f} %")
    print(f"Décision        : {r.decision.value}")
    print()
    print("Points forts :")
    for point in r.points_forts:
        print(f"  + {point}")
    if not r.points_forts:
        print("  (aucun)")
    print()
    print("Écarts :")
    for ecart in r.ecarts:
        print(f"  - {ecart}")
    if not r.ecarts:
        print("  (aucun)")
    print()
    print("Compétences manquantes :")
    for competence in r.competences_manquantes:
        print(f"  - {competence}")
    if not r.competences_manquantes:
        print("  (aucune)")
    print()
    print("Résumé :")
    print(a.resume)
    print("=" * 60)


def _commande_import_mission(args: argparse.Namespace) -> None:
    try:
        settings = get_settings()
    except ValidationError:
        print(
            "Erreur : ANTHROPIC_API_KEY n'est pas configurée (config/.env ou variable d'environnement).",
            file=sys.stderr,
        )
        sys.exit(1)

    email = args.email or settings.mission_agent_user_email
    if not email:
        print(
            "Erreur : --email requis (ou variable d'environnement MISSION_AGENT_USER_EMAIL).",
            file=sys.stderr,
        )
        sys.exit(1)

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    analyseur = AnthropicAnalyseurMission(client, settings.anthropic_model)

    try:
        with session_scope() as session:
            resultat = importer_mission(
                url=args.url, texte=args.texte, email=email, analyseur=analyseur, session=session
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


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = _parse_args(argv)

    if args.commande == "import-mission":
        _commande_import_mission(args)


if __name__ == "__main__":
    main()
