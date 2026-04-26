#! /usr/bin/env python3

import argparse
import pathlib
import re
import sys
import spacy

nlp = spacy.load("fr_core_news_sm")

def read(filename, encoding="utf-8"):
    return pathlib.Path(filename).read_text(encoding=encoding)

def nettoyage_simplifie(texte):
    texte = re.sub(r"\s+", " ", texte)
    return texte.strip()

def extraire_sequence_pos(texte):
    doc = nlp(nettoyage_simplifie(texte))
    pos_list = [token.pos_ for token in doc if token.pos_]
    return " ".join(pos_list)

def process_ngram_merged(corpus_path, out_path=None):
    base_dir = pathlib.Path(corpus_path)
    out_path = out_path or base_dir / "total_pos_sequence.arff"

    target_classes = ["apprenants", "natifs"]
    all_data = {cls: [] for cls in target_classes}


    for txt_file in base_dir.rglob("*.txt"):
        if txt_file.name.startswith("."):
            continue
        parent_name = txt_file.parent.name
        if parent_name in target_classes:
            all_data[parent_name].append(txt_file)

    contenu_arff = ["@relation corpus_total_ngram"]
    contenu_arff.append("@attribute 'pos_sequence' string")
    contenu_arff.append(f"@attribute 'xClasse' {{{','.join(target_classes)}}}")
    contenu_arff.append("@data")

    for etiquette in target_classes:
        for f in all_data[etiquette]:
            texte_brut = read(f)
            sequence = extraire_sequence_pos(texte_brut)
            sequence_echappee = sequence.replace('"', '\\"')
            contenu_arff.append(f'"{sequence_echappee}",{etiquette}')

    with open(out_path, "w", encoding="utf-8") as f_sortie:
        f_sortie.write("\n".join(contenu_arff))
        f_sortie.write("\n")

def main():
    parser = argparse.ArgumentParser(description="Générer un ARFF total pour N-gramme")
    parser.add_argument("corpus_path", type=str, help="Le dossier racine (data/corpus/)")
    parser.add_argument("out_path", type=str, nargs="?", default=None)

    args = parser.parse_args()
    process_ngram_merged(args.corpus_path, args.out_path)

if __name__ == "__main__":
    main()
