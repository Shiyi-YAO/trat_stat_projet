import os
import spacy
import pathlib

nlp = spacy.load("fr_core_news_sm")
chemin_projet = pathlib.Path(__file__).parent.parent
entree = chemin_projet / "data" / "corpus"
sortie = chemin_projet / "data" / "corpus_pos"

def transformer_corpus_en_pos():

    compteur = 0

    for racine, dirs, fichiers in os.walk(entree):
        for nom_fichier in fichiers:
            if nom_fichier.endswith(".txt"):
                chemin_complet_entree = os.path.join(racine, nom_fichier)
                chemin_relatif = os.path.relpath(racine, entree)
                dossier_cible = os.path.join(sortie, chemin_relatif)

                if not os.path.exists(dossier_cible):
                    os.makedirs(dossier_cible)

                chemin_complet_sortie = os.path.join(dossier_cible, nom_fichier)

                with open(chemin_complet_entree, 'r', encoding='utf-8') as f_entree:
                    texte = f_entree.read()
                    doc = nlp(texte)

                # Extraction des étiquettes UPOS (Universal POS)
                liste_pos = [jeton.pos_ for jeton in doc if not jeton.is_punct and not jeton.is_space]
                sequence_pos = " ".join(liste_pos)

                with open(chemin_complet_sortie, 'w', encoding='utf-8') as f_sortie:
                    f_sortie.write(sequence_pos)

                compteur += 1

if __name__ == "__main__":
    transformer_corpus_en_pos()
