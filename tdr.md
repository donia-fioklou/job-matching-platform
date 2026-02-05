Projet pro : Plateforme intelligente d’aide à
la candidature par IA
1. Contexte général du projet
Aujourd’hui, les candidats à l’emploi font face à plusieurs difficultés :
● un très grand nombre d’offres dispersées sur différents sites,
● des descriptions de postes parfois longues et ambiguës,
● des exigences peu claires sur les compétences réellement attendues,
● la difficulté d’adapter son CV à chaque offre,
● le manque de feedback objectif sur la pertinence de son profil.
L’objectif de ce projet est de concevoir une plateforme intelligente basée sur l’IA capable de
:
● collecter des offres d’emploi depuis différentes sources,
● analyser et comprendre ces offres,
● comparer automatiquement le profil d’un candidat avec les attentes du poste,
● accompagner le candidat dans la préparation de sa candidature (CV, conseils,
recommandations).
Ce projet permet aux étudiants de mettre en pratique l’ensemble de la chaîne Data & IA,
depuis la collecte des données jusqu’à la création d’un assistant intelligent.
2. Objectif pédagogique du projet
À l’issue du projet, les étudiants seront capables de :
● comprendre comment collecter et structurer des données réelles (offres d’emploi),
● mettre en place un pipeline de traitement de données,
● utiliser des techniques de NLP (traitement automatique du langage),
● appliquer la vectorisation sémantique (embeddings),
● exploiter une base de données vectorielle,
● concevoir une IA capable de raisonner à partir de données,
● développer un MVP (Minimum Viable Product) fonctionnel et cohérent.
3. Vision globale de la solution
La solution développée est une plateforme d’aide à la candidature qui fonctionne de la
manière suivante :
1. Le système collecte des offres d’emploi depuis plusieurs sources.
2. Les offres sont nettoyées, structurées et stockées.
3. Les descriptions des offres et les CV des candidats sont transformés en vecteurs
numériques.
4. Le système compare le profil du candidat aux offres disponibles.
5. Une IA analyse les écarts et les correspondances.
6. Le candidat reçoit des recommandations claires et exploitables.
4. Description détaillée des fonctionnalités
4.1 Collecte des offres d’emploi (Data Ingestion)
La première étape du projet consiste à sourcer les offres d’emploi à partir de différentes
sources :
● sites d’emploi en ligne,
● plateformes locales ou régionales,
● fichiers de données fournis (CSV, JSON) pour les tests.
Les étudiants devront extraire les informations essentielles :
● intitulé du poste,
● description du poste,
● compétences requises,
● localisation,
● type de contrat.
Cette étape permet d’introduire les notions de scraping, APIs et ingestion de données.
4.2 Stockage et structuration des données
Une fois collectées, les offres sont stockées dans une base de données.
Deux types de stockage sont utilisés :
● une base de données classique pour les informations structurées (ex : PostgreSQL,
MongoDB),
● une base vectorielle pour stocker les représentations numériques des textes.
Les étudiants apprendront à concevoir un schéma de données clair et exploitable.
4.3 Analyse sémantique et vectorisation
Les descriptions des offres d’emploi et les CV des candidats sont des textes non structurés.
Pour permettre à la machine de les comprendre, ils sont transformés en vecteurs numériques
à l’aide de modèles de langage (embeddings).
Cette étape permet :
● de comparer les textes sur le plan du sens et non uniquement par mots-clés,
● d’identifier les offres les plus proches du profil du candidat.
C’est une étape centrale du projet.
4.4 Matching entre profil candidat et offres d’emploi
À partir des vecteurs, le système calcule un score de correspondance entre :
● le CV du candidat,
● chaque offre d’emploi.
Le matching prend en compte :
● la similarité sémantique,
● les compétences clés,
● le niveau d’expérience attendu.
Le résultat permet de classer les offres par pertinence.
4.5 IA d’analyse et de raisonnement
Une fois le matching effectué, une IA de raisonnement intervient pour :
● expliquer ce que l’entreprise attend réellement du candidat,
● identifier les points forts du profil,
● détecter les compétences manquantes ou insuffisantes,
● recommander ou non de postuler à l’offre.
L’IA ne se contente pas de générer du texte :
elle s’appuie sur des données concrètes (offre + CV) pour produire une analyse argumentée.
4.6 Aide à la préparation du CV
La plateforme propose ensuite une assistance ciblée :
● reformulation de certaines parties du CV pour une offre donnée,
● suggestions de compétences à mettre en avant,
● recommandations d’amélioration du profil.
L’objectif n’est pas de falsifier le CV, mais de mieux valoriser les compétences existantes.
4.7 Interface utilisateur (MVP)
Une interface simple est mise en place pour interagir avec le système :
● téléchargement du CV,
● choix ou recherche d’un type de poste,
● affichage des offres pertinentes,
● visualisation du score et des recommandations.
L’interface est volontairement minimale afin de se concentrer sur la logique Data & IA.
5. Périmètre du MVP (ce qui est attendu)
Le MVP du projet doit permettre :
● la collecte de plusieurs offres d’emploi,
● l’analyse sémantique des offres et des CV,
● le matching intelligent,
● des recommandations claires pour le candidat.
6. Éléments volontairement exclus du MVP
Pour des raisons de complexité et d’éthique, le MVP n’inclut pas :
● le remplissage automatique de formulaires sur des sites externes,
● l’envoi réel de candidatures,
● des promesses de recrutement automatique.
Ces fonctionnalités peuvent être envisagées comme évolutions futures.
7. Compétences développées par les étudiants
À travers ce projet, les étudiants développent :
● des compétences techniques (Python, NLP, bases de données),
● une compréhension des systèmes IA modernes,
● une approche produit orientée utilisateur,
● une réflexion éthique sur l’usage de l’IA dans le recrutement.
8. Conclusion
Ce projet vise à montrer que l’IA n’est pas seulement un outil de génération de texte, mais un
système intelligent complet, capable de :
● comprendre des données complexes,
● raisonner,
● assister l’humain dans des décisions importantes.
Il constitue un excellent cas pratique pour relier théorie, technique et impact réel.