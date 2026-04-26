# Projet
- Ce projet vise à identifier automatiquement le statut d'un auteur (locuteur natif ou apprenant de FLE) à partir de caractéristiques syntaxiques (étiquettes POS).
## 1. Préparation
```
git clone git@github.com:Shiyi-YAO/trat_stat_projet.git
```
```
cd trat_stat_projet
```
- Nous utilisons un environnement virtuel pour éviter les conflits de versions. Une fois l'environnement activé, installez les outils nécessaires.
```
python3 -m venv venv
```
```
source venv/bin/activate
```
```
uv pip install spacy pathlib
```
```
python3 -m spacy download fr_core_news_sm
```
## 2. Préparation du corpus
```
python3 construire_corpus_apprenants.py
```
```
python3 construire_corpus_natifs.py
```
```
python3 scripts/transformation_pos.py ./data/corpus/
```
## 3. Génération des fichiers pour Weka(.arff)
- Générer le fichier d'entraînement (Train)
```
python3 scripts/vectorisation.py data/corpus/train/ data/arff/frequences/train_frequences.arff --representation occurrences
```
- Générer le fichier de test (Test)
```
python3 scripts/vectorisation.py data/corpus/test/ data/arff/frequences/train_frequences.arff --representation occurrences --lexicon data/arff/frequences/test_frequences.arff
```
- Générer le fichier ARFF pour l'analyse par N-grammes
```
python3 scripts/vectorisation_ngram.py ../data/corpus/ data/arff/total_pos.arff
```


- Ouvrez les fichiers .arff générés dans Weka, choisissez l'algorithme et lancez le test !
