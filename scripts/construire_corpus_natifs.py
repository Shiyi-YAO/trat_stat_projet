#!/usr/bin/env python3
# pip install pypdf

# cd scripts
# python construire_corpus_natifs.py


from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

# Ces 3 fichiers sont traités par défaut.
DEFAULT_PDFS = [
    "../ceaal2/10/Productions de scripteurs natifs/Essai argumenté/Productions de francophones natifs/Essai argumenté_francophones natifs.pdf",
    "../ceaal2/10/Productions de scripteurs natifs/Essai argumenté/Productions de francophones natifs/Francophones natifs_essai argumenté_2025.pdf",
    "../ceaal2/10/Productions de scripteurs natifs/Lettre formelle/Productions de francophones natifs/Productions de francophones natifs_lettre formelle.pdf",
]

TITLE_RE = re.compile(
    r"Partir\s+étudier\s+à\s+l[’']étranger,\s*pour\s+ou\s+contre\s*\?",
    re.IGNORECASE,
)

DOC_HEADER_PATTERNS = [
    re.compile(r"^Essais?\s+argument[ée]?\s*[–-]\s*francophones\s+natifs\s*$", re.IGNORECASE),
    re.compile(r"^Productions?\s+des?\s+francophones\s+natifs(?:\s+20\d{2}(?:-\d{4})?)?\s*$", re.IGNORECASE),
    re.compile(r"^Sujet\s*:", re.IGNORECASE),
]

METADATA_PATTERNS = [
    re.compile(r"^[•\-−]?\s*Texte\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*FR_L1_\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Participant\s*\d+\s*:\s*.*$", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Sexe\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Age\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Nationalité\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Prénom\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Langue\s+maternelle\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Langue\s+parlée\s+avec\s+.*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Langue\s+parlée\s+avec\s+parents.*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Langue\s+parlée\s+avec\s+conjoints.*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Langue\s+maternelle\s+des\s+parents\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Leur\s+langue\s+maternelle\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Pays\s+de\s+résidence\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Pays\s+de\s+résidence\s+au\s+moment\s+de\s+l[’']enquête\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Etudes?\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Etudes?\s+en\s+cours\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Niveau\s+d[’']études\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*LM\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Autres\s+langues(?:\s+connues|\s+apprises)?\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Langues?\s+étrangères\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Usage\s+des\s+langues\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Nombre\s+de\s+livres\s+lus\s+en\s+français\s+par\s+an\s*:", re.IGNORECASE),
    re.compile(r"^[•\-−]?\s*Séjours?\s+à\s+l[’']étranger.*:", re.IGNORECASE),
]

# Dans le premier PDF, le nom de l'auteur figurait sur une ligne séparée ; il n'a donc été supprimé qu'en tant que métadonnée dans la section « avant le début de l'article ».
NAME_ONLY_RE = re.compile(r"^[•\-−]?\s*[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’\- ]{1,60}\s*$")
METADATA_CONTINUATION_RE = re.compile(r"^[A-ZÀ-ÖØ-Ý][A-Za-zÀ-ÖØ-öø-ÿ'’\- /]{1,40}\s*:")


@dataclass
class ExtractedArticle:
    source_pdf: Path
    page_number: int
    text: str


def clean_text(raw: str) -> str:
    text = raw.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_leading_bullet(line: str) -> str:
    return re.sub(r"^[•\-−]\s*", "", line.strip())


def is_doc_header(line: str) -> bool:
    return any(p.match(line) for p in DOC_HEADER_PATTERNS)


def is_metadata_line(line: str) -> bool:
    return any(p.match(line) for p in METADATA_PATTERNS)


def collapse_blank_lines(lines: list[str]) -> list[str]:
    out: list[str] = []
    last_blank = True
    for line in lines:
        if not line.strip():
            if not last_blank:
                out.append("")
            last_blank = True
        else:
            out.append(line.rstrip())
            last_blank = False
    while out and not out[-1].strip():
        out.pop()
    return out


def extract_article_from_page(raw_text: str) -> str | None:
    text = clean_text(raw_text)
    if not text:
        return None

    title_match = TITLE_RE.search(text)
    if title_match:
        # Premier PDF : Extrait du titre de l’article, supprimant intégralement toutes les informations biographiques.
        article = text[title_match.start():].strip()
        return article or None

    lines = [strip_leading_bullet(line) for line in text.splitlines()]
    lines = [line.strip() for line in lines]

    kept: list[str] = []
    started = False
    saw_metadata = False

    for line in lines:
        if not line:
            if started:
                kept.append("")
            continue

        if not started:
            if is_doc_header(line):
                continue

            if is_metadata_line(line):
                saw_metadata = True
                continue

            if saw_metadata and NAME_ONLY_RE.match(line):
                continue

            if saw_metadata and METADATA_CONTINUATION_RE.match(line):
                continue

            if not saw_metadata:
                # S'il n'y a pas de métadonnées ni de titre d'article, et qu'il s'agit généralement d'une page de couverture/d'introduction, passer.
                continue

            # Deuxième et troisième PDF : après la fin des métadonnées, la première ligne non métadonnée marque le début du texte principal.
            started = True
            kept.append(line)
        else:
            kept.append(line)

    kept = collapse_blank_lines(kept)
    article = "\n".join(kept).strip()
    return article or None


def extract_articles_from_pdf(pdf_path: Path) -> list[ExtractedArticle]:
    reader = PdfReader(str(pdf_path))
    articles: list[ExtractedArticle] = []

    for page_number, page in enumerate(reader.pages, start=1):
        raw = page.extract_text() or ""
        article = extract_article_from_page(raw)
        if article:
            articles.append(
                ExtractedArticle(
                    source_pdf=pdf_path,
                    page_number=page_number,
                    text=article,
                )
            )

    return articles


def save_articles(
    articles: list[ExtractedArticle],
    output_dir: Path,
    train_count: int,
) -> None:
    train_dir = output_dir / "train" / "natifs"
    test_dir = output_dir / "test" / "natifs"
    train_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    for idx, article in enumerate(articles, start=1):
        target_dir = train_dir if idx <= train_count else test_dir
        out_file = target_dir / f"t{idx}.txt"
        out_file.write_text(article.text + "\n", encoding="utf-8")
        print(f"[OK] t{idx}.txt <- {article.source_pdf.name} page {article.page_number} -> {target_dir}")


def resolve_pdf_paths(pdf_args: Iterable[str]) -> list[Path]:
    if pdf_args:
        pdfs = [Path(p) for p in pdf_args]
    else:
        pdfs = [Path(name) for name in DEFAULT_PDFS]

    missing = [str(p) for p in pdfs if not p.exists()]
    if missing:
        raise SystemExit("fichier n'existe pas:\n" + "\n".join(missing))

    return pdfs


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Traite simultanément plusieurs PDF et enregistre les textes sous les noms t1.txt, t2.txt, ... ; "
            "place les 80 premiers dans train/natifs et le reste dans test/natifs."
        )
    )
    parser.add_argument(
        "pdfs",
        nargs="*",
        help=(
            "Liste des chemins d'accès aux fichiers PDF. Si aucune valeur n'est fournie, les 3 fichiers du répertoire courant seront traités par défaut.：\n"
            + "\n".join(DEFAULT_PDFS)
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("../data/corpus"),
        help="Répertoire racine de sortie, par défaut : ../data/corpus",
    )
    parser.add_argument(
        "--train-count",
        type=int,
        default=80,
        help="Les N premiers fichiers txt sont placés dans train/natifs (par défaut : 80)",
    )
    args = parser.parse_args()

    pdf_paths = resolve_pdf_paths(args.pdfs)

    all_articles: list[ExtractedArticle] = []
    for pdf_path in pdf_paths:
        articles = extract_articles_from_pdf(pdf_path)
        print(f"[INFO] {pdf_path.name} : {len(articles)} textes extraits")
        all_articles.extend(articles)

    if not all_articles:
        raise SystemExit("Aucun article n'a été extrait du PDF")

    save_articles(all_articles, args.output_dir, args.train_count)

    print("\nTerminé.")
    print(f"Nombre total de textes : {len(all_articles)}")
    print(f"train : {min(args.train_count, len(all_articles))}")
    print(f"test : {max(0, len(all_articles) - args.train_count)}")
    print(f"Dossier de sortie : {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
