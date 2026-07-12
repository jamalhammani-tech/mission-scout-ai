"""Extraction de texte brut à partir d'un CV PDF ou DOCX (MVP — pas d'OCR)."""

from pathlib import Path

FORMATS_SUPPORTES = {".pdf", ".docx"}


def extraire_texte(chemin: Path) -> str:
    suffixe = chemin.suffix.lower()
    if suffixe == ".pdf":
        texte = _extraire_pdf(chemin)
    elif suffixe == ".docx":
        texte = _extraire_docx(chemin)
    else:
        raise ValueError(f"Format non supporté : {suffixe!r} (attendu : {sorted(FORMATS_SUPPORTES)})")

    if not texte.strip():
        raise ValueError(
            f"Aucun texte exploitable extrait de {chemin} (PDF scanné sans OCR ? document vide ?)"
        )
    return texte


def _extraire_pdf(chemin: Path) -> str:
    import pdfplumber

    with pdfplumber.open(chemin) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    return "\n".join(pages).strip()


def _extraire_docx(chemin: Path) -> str:
    import docx

    document = docx.Document(str(chemin))
    paragraphes = [p.text for p in document.paragraphs]
    return "\n".join(paragraphes).strip()
