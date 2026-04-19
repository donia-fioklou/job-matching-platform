# Note Explicative - Plateforme Intelligente d'Aide à la Candidature par IA

> **Informations Projet**
> 
> **Date :** 21 février 2026  
> **Projet :** Job Matching Platform - Phase 1 (Data Foundation)  
> **Statut :** Infrastructure de base déployée, préparation phase IA  

## **Résumé Exécutif**

> **Vision Projet**
> 
> Développement d'une **plateforme intelligente d'aide à la candidature** basée sur l'IA pour le marché togolais et africain. Ce projet vise à créer un système complet qui collecte les offres d'emploi, analyse sémantiquement les correspondances entre profils candidats et postes, et accompagne intelligemment les candidats dans leur recherche d'emploi.
> 
> **Phase actuelle :** Fondations data solides avec architecture moderne pour supporter les futures capacités d'IA.

## **Vision Globale du Projet (TDR)**

> **Architecture Target**
> 
> La solution finale fonctionnera selon cette chaîne de valeur :
> ```
> Collecte Offres → Vectorisation Sémantique → Matching IA → Analyse Profil → Recommandations Personnalisées
> ```

### **Workflow Complet**

1. **Collecte** des offres d'emploi multi-sources
2. **Transformation** en vecteurs sémantiques (embeddings)
3. **Matching intelligent** profil candidat ↔ offres
4. **IA d'analyse** pour comprendre les écarts/correspondances
5. **Recommandations** personnalisées et aide à la préparation CV

## **Réalisations Actuelles - Phase 1 : Fondations Data**

### **Infrastructure de Collecte Déployée (100% Opérationnelle)**

> **Architecture Technique**
> 
> ```
> Sources d'Emploi → Airflow (ETL) → PostgreSQL/Supabase → FastAPI → Future IA Pipeline
> ```

### **Justifications Techniques**

> **Choix Stratégiques**
> 
> - **Apache Airflow** : Orchestration robuste nécessaire pour gérer 5+ sources avec fréquences différentes et préparer l'intégration future de pipelines ML
> - **PostgreSQL via Supabase** : Base relationnelle stable pour données structurées + capacités vectorielles natives pour les embeddings futurs
> - **FastAPI** : Performance élevée + génération automatique de documentation + support natif des modèles Pydantic (compatibles avec les futures pipelines ML)
> - **Docker** : Environnement reproductible essentiel pour déploiement des modèles IA

> **Anticipation Future**
> 
> Cette architecture anticipe intentionnellement :
> - Intégration de modèles de machine learning
> - Stockage de vecteurs sémantiques (embeddings)
> - Scaling horizontal pour traitement intensif NLP

### **Sources de Données Opérationnelles**

> **Performance Collecte**
> 
> **Total collecté** : ~600 offres/jour avec déduplication automatique

| Source | Type | Fréquence | Volume/jour | Justification |
|--------|------|-----------|-------------|---------------|
| **EmploiTogo.info** | Scraping | Quotidien | ~200 offres | Source principale marché local |
| **GoAfricaOnline** | Scraping | Quotidien | ~150 offres | Couverture multinationale |
| **LuCreatif** | Scraping | Quotidien | ~80 offres | Secteur créatif/digital |
| **Emploi.tg** | Scraping | Quotidien | ~120 offres | Complémentarité locale |
| **JSearch API** | API REST | Horaire | ~50 offres | Validation internationale |

### **Innovation Technique : Architecture Two-Phase pour IA**

> **Stratégie Optimisation**
> 
> **Stratégie technique développée pour optimiser le pipeline vers l'IA :**

**Phase 1 - Collecte Rapide (Actuellement déployée)**
- Extraction métadonnées critiques : titre, entreprise, localisation
- Déduplication immédiate par URL unique
- Indexation rapide pour disponibilité données

**Phase 2 - Enrichissement Détaillé (Optimisée pour NLP)**
- Extraction descriptions complètes
- Nettoyage et structuration pour tokenisation
- Préparation format compatible embeddings

> **Avantages pour IA**
> 
> Cette architecture sépare délibérément la **collecte de base** de l'**enrichissement sémantique**, permettant :
> 
> - **Performance** : Données de base disponibles immédiatement pour MVP
> - **Flexibilité** : Réentraînement de modèles sans impact sur la collecte
> - **Coût-efficacité** : Traitement NLP coûteux uniquement sur descriptions validées
> - **Monitoring** : Metrics séparées pour optimisation indépendante des phases

## **Gap Analysis : Réalisé vs TDR Target**

### **Composants Opérationnels (Phase 1 - 100%)**

| Fonctionnalité TDR | Statut Actuel | Implementation |
|-------------------|---------------|----------------|
| Collecte multi-sources | **FAIT** | 5 sources actives, 600+ offres/jour |
| Stockage structuré | **FAIT** | PostgreSQL + schema optimisé |
| API d'exposition | **FAIT** | FastAPI avec 80% endpoints |
| Pipeline ETL automatisé | **FAIT** | Airflow DAGs opérationnels |

### **Composants à Développer (Phase 2 - Planning)**

| Fonctionnalité TDR | Statut | Technologies Prévues |
|-------------------|--------|---------------------|
| **Analyse sémantique** | En conception | Sentence-BERT + pgvector |
| **Vectorisation** | Sprint suivant | HuggingFace Transformers |
| **Matching IA** | Q2 2026 | Cosine similarity + fine-tuning |
| **IA raisonnement** | Q2 2026 | OpenAI GPT-4 + RAG |
| **Interface MVP** | Q2 2026 | React + TailwindCSS |

## **Roadmap Technique Vers l'IA (Phases 2-4)**

### **Phase 2 - Traitement Sémantique (Q1-Q2 2026)**

> **Technologies sélectionnées**
> 
> - **Sentence-BERT** : Modèle pré-entraîné français optimisé pour embeddings de phrases
> - **pgvector** : Extension PostgreSQL pour stockage et requêtes vectorielles natives
> - **FAISS** : Index de similarité Facebook pour recherche rapide à large échelle

```python
# Pipeline de vectorisation
sentence_model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased')
job_embeddings = model.encode(job_descriptions)
candidate_embeddings = model.encode(cv_content)
similarity_scores = cosine_similarity(candidate_embeddings, job_embeddings)
```

> **Justification choix**
> 
> - Support multilingue (français/anglais) adapté au contexte togolais
> - Performance optimisée pour textes courts à moyens (descriptions d'offres)
> - Intégration native avec l'architecture PostgreSQL existante

### **Phase 3 - Matching Intelligent (Q2-Q3 2026)**

> **Algorithme de matching multicritères**
> 
> - **Similarité sémantique** (40%) : Sentence-BERT + cosine similarity
> - **Compétences techniques** (35%) : NER + matching exact/fuzzy
> - **Expérience niveau** (15%) : Extraction patterns + scoring
> - **Géolocalisation** (10%) : Pondération distance/préférences

> **IA de raisonnement**
> 
> - **RAG (Retrieval Augmented Generation)** avec LangChain
> - **Modèle base** : GPT-4 ou Claude-3 pour génération contextuelle
> - **Base de connaissances** : Embeddings des meilleures pratiques RH

### **Phase 4 - Assistant IA Complet (Q3-Q4 2026)**

> **Capacités d'assistance avancées**
> 
> - **Analyse CV automatique** : Extraction structurée compétences/expérience
> - **Recommandations personnalisées** : Suggestions d'amélioration ciblées
> - **Simulation d'entretien** : Chatbot entraîné sur questions sectorielles
> - **Veille métier** : Alertes automatiques nouvelles offres matchées

## **Justifications des Choix Technologiques**

### **Pourquoi cette stack pour l'IA ?**

> **1. Sentence-BERT vs Word2Vec/TF-IDF**
> 
> - Compréhension contextuelle vs mots-clés isolés
> - Performance supérieure sur textes RH (validé par benchmarks)
> - Support natif multilangue essentiel pour contexte African

> **2. PostgreSQL + pgvector vs Pinecone/Weaviate**
> 
> - Réduction coûts infrastructure (pas de base vectorielle séparée)
> - Cohérence transactionnelle données structurées + vecteurs
> - Expertise équipe déjà acquise sur PostgreSQL

> **3. FastAPI + LangChain vs Flask + OpenAI direct**
> 
> - Performance async nécessaire pour appels LLM multiples
> - LangChain pour gestion complexe des prompts et chaînage
> - Monitoring et observabilité intégrés

> **4. RAG vs Fine-tuning complet**
> 
> - Coût développement/entraînement 10x inférieur
> - Mise à jour données en temps réel vs réentraînement
> - Contrôle précis des sources de connaissance

### **Architecture Target Finale (Q4 2026)**

```
User Interface (React)
    ↓
FastAPI Gateway
    ↓
┌─────────────────┬─────────────────┬─────────────────┐
│   Data Pipeline │  ML Pipeline    │   AI Assistant  │
│   (Airflow)     │  (BERT/FAISS)  │   (LangChain)   │
└─────────────────┴─────────────────┴─────────────────┘
    ↓
PostgreSQL + pgvector (Unified Storage)
```

## **Impact Business et Innovation**

### **Différenciation Marché**

> **Positionnement Unique**
> 
> Transformation d'un **agrégateur d'offres classique** vers une **plateforme d'IA d'aide à la candidature**, positionnement unique sur le marché africain.

### **Métriques de Succès Définies**

> **Phase 1 (Actuelle) - Data Foundation**
> 
> - Volume de données : 600+ offres/jour collectées
> - Qualité : <5% de doublons post-déduplication
> - Performance : 95% uptime pipeline de collecte
> - Couverture : 5 sources principales marché togolais

> **Phase 2 (Target Q2 2026) - IA Matching**
> 
> - Précision matching : >80% sur échantillon test
> - Temps de traitement : <3 secondes par matching
> - Satisfaction utilisateur : >4/5 sur pertinence recommandations

> **Phase 3 (Target Q4 2026) - Assistant Complet**
> 
> - Adoption : 1000+ utilisateurs actifs mensuels
> - Efficacité : 50% réduction temps préparation candidature
> - Impact placement : tracking taux de réponse positive

### **Avantages Concurrentiels Développés**

> **Moats Stratégiques**
> 
> 1. **Technical Moat** : Architecture hybrid data + IA difficile à répliquer
> 2. **Data Network Effect** : Plus d'utilisateurs → Meilleur modèle → Plus d'utilisateurs
> 3. **Expertise locale** : Modèles fine-tunés contexte africain
> 4. **Platform Integration** : API prête pour partenariats écosystème RH

### **Risques Techniques et Mitigation**

| Risque Technique | Probabilité | Impact | Stratégie de Mitigation |
|------------------|-------------|--------|------------------------|
| **Dérive performance modèles** | Moyen | Élevé | Monitoring continu + réajustement automatique |
| **Coût infrastructure IA** | Moyen | Moyen | Optimisation requêtes + caching intelligent |
| **Biais algorithme matching** | Faible | Élevé | Tests A/B systématiques + diverse dataset |
| **Évolution sites sources** | Élevé | Faible | Architecture modulaire + monitoring breakage |

---

## **Conclusion Stratégique**

> **Vision**
> 
> Cette plateforme représente une **innovation majeure dans l'écosystème RH africain**, transformant la recherche d'emploi d'un processus manuel et fastidieux vers une **expérience assistée par IA**.

> **État Actuel**
> 
> **Phase 1 accomplie** : Fondations techniques solides avec architecture moderne prête pour l'IA.

> **Perspectives**
> 
> **Phase 2-4 planifiées** : Intégration progressive de capacités d'intelligence artificielle pour créer le premier **assistant de candidature intelligent** adapté au contexte africain.

> **Positionnement**
> 
> **Positionnement marché** : Leader technologique régional avec architecture différenciante et barrières à l'entrée élevées.

---

> **Document préparé par** : [Votre Nom]  
> **Contact** : [Votre Email]  
> **Référence TDR** : Plateforme intelligente d'aide à la candidature par IA