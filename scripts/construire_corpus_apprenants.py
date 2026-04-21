import pdfplumber
import os
import re

def nettoyer_texte_page(page_pdf):
    """
    Extrait le texte d'une page et ne conserve que le corps de la lettre.
    Supprime les métadonnées (Participant, Langue, etc.) et les tirets.
    """
    texte_brut = page_pdf.extract_text()
    if not texte_brut:
        return None

    lignes = texte_brut.split('\n')
    lignes_propres = []

    motif_filtre = re.compile(r'^([-\u2013\u2014\u2212\u2022]|Participant|Langue|Age|Sexe|Niveau|Autres|Nombre|Séjours|Diplôme|Spécialité|Pays|Nationalité|Etudes|Usage|Nombres|F/H)', re.IGNORECASE)

    for ligne in lignes:
        segment = ligne.strip()

        if not segment:
            continue

        if motif_filtre.match(segment):
            continue

        if len(segment) < 50 and ':' in segment:
            continue

        lignes_propres.append(segment)

    return "\n".join(lignes_propres) if lignes_propres else None

def executer_preparation():
    liste_chemins_pdf = [
        "../ceaal2/10/Productions d'apprenants de FLE/Lettre officielle/Apprenants sinophones du FLE_contexte hétéroglotte/Productions des apprenants en Chine.pdf",
        "../ceaal2/10/Productions d'apprenants de FLE/Lettre officielle/Apprenants sinophones du FLE_contexte hétéroglotte/Apprenants sinophones de français en contexte hétéroglotte_2025.pdf",
        "../ceaal2/10/Productions d'apprenants de FLE/Lettre officielle/Apprenants russophones du FLE/Apprenants russophones du FLE.pdf",
        "../ceaal2/10/Productions d'apprenants de FLE/Lettre officielle/Apprenants russophones du FLE/Apprenants_russophones_contexte hétéroglotte_Lettre formelle_2024.pdf"
    ]

    rep_apprentissage = "../data/corpus/train/apprenants/"
    rep_test = "../data/corpus/test/apprenants/"


    compteur_total = 0

    for chemin in liste_chemins_pdf:
        if not os.path.exists(chemin):
            print(f"Fichier introuvable, passage : {chemin}")
            continue

        print(f"Traitement de : {os.path.basename(chemin)}")

        try:
            with pdfplumber.open(chemin) as document_pdf:
                # On saute la première page de chaque PDF (index 0)
                for page in document_pdf.pages[1:]:
                    corps_final = nettoyer_texte_page(page)

                    if corps_final:
                        compteur_total += 1

                        # Répartition : les 80 premiers dans 'train', les suivants dans 'test'
                        if compteur_total <= 80:
                            dossier_cible = rep_apprentissage
                        else:
                            dossier_cible = rep_test

                        nom_fichier_txt = f"t{compteur_total}.txt"
                        chemin_sortie = os.path.join(dossier_cible, nom_fichier_txt)

                        with open(chemin_sortie, 'w', encoding='utf-8') as fichier_txt:
                            fichier_txt.write(corps_final)

        except Exception as e:
            print(f"Erreur lors de la lecture de {chemin} : {e}")

    print(f"\nTraitement terminé.")
    print(f"Total de fichiers générés : {compteur_total}")
    print(f"Fichiers dans TRAIN : {min(compteur_total, 80)}")
    print(f"Fichiers dans TEST : {max(0, compteur_total - 80)}")

if __name__ == "__main__":
    executer_preparation()
