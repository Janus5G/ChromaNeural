# ChromaNeural

[English](../en/ChromaNeural-Overview.md) · [Dansk](../da/ChromaNeural-Overview-DA.md) · [Deutsch](../de/ChromaNeural-Overview.md) · [Français](ChromaNeural-Overview.md) · [日本語](../ja/ChromaNeural-Overview.md) · [简体中文](../zh-CN/ChromaNeural-Overview.md) · [हिन्दी](../hi-IN/ChromaNeural-Overview.md)
## Présentation

Documentation ChromaNeural 0.2.21-rc.2 | Candidat non publié | 3 octobre 2026

**État de la documentation rc.2 :** Ce candidat n’a pas été publié. La localisation et l’i18n extensible ont passé la vérification locale ; l’acceptation des compilations et paquets natifs rc.2 reste en attente. Les preuves d’installation, de plateforme, LAN/WAN, d’inférence et de service en production ci-dessous sont historiques et concernent rc.1, sauf mention rc.2 explicite. Les téléchargements rc.1 ne fournissent pas la localisation rc.2.

### Intelligence locale. Collaboration explicitement autorisée.

ChromaNeural relie travail d’IA local, file de travail persistante et communication entre pairs approuvés. Vous choisissez les données à traiter et les contributions partageables. Une réponse n’est ni correcte ni vérifiée du seul fait qu’un modèle l’a produite.

Le profil de collaboration pris en charge est la proposition de code. Ce n’est pas une place de marché acceptant et exécutant automatiquement des tâches distantes arbitraires. Le bureau n’offre pas encore de bouton général pour soumettre tout type de problème ou d’étude.

![Véritable client Windows, participation arrêtée, sans compte ni données privées.](../images/chroma-neural-overview.png)

### Langues de rc.2

Le client unique inclut en, da, de, fr, ja, zh-CN et hi-IN. L’anglais est la langue par défaut et de repli. Le sélecteur latéral change les textes applicatifs et mémorise le choix. Le registre extensible permet de futurs catalogues sans clients séparés ni logique d’interface dupliquée. Le guide utilisateur détaille préférences et remplacement au lancement.

### Fonctions utilisables aujourd’hui

- Consulter la participation et enregistrer les préférences de ressources.
- Vérifier la réponse de l’API publique du backend.
- Utiliser l’IA locale existante pour proposer des modifications d’un fichier choisi.
- Traiter les tâches locales déjà autorisées avec le worker de fond du profil Windows pris en charge.
- Utiliser la CLI avancée existante pour une collaboration avec des pairs explicitement approuvée et corrélée.

<!-- page -->
## De l’entrée au résultat

Le partage général des ressources reste désactivé. Installation et connexion réussie n’accordent ni admission réseau, ni tâches, ni ChromaPoints.

### 1. Entrée et permission

Une tâche existante identifie entrée source, instruction et fournisseur/modèle choisi. Traitement local et réseau exigent leurs autorisations respectives. Ouvrir un dossier n’autorise pas son partage.

### 2. File et traitement

La file SQLite existante préserve identité et état des tâches. Un bail réserve le travail à un worker. Pause, annulation, arrêt et redémarrage contrôlés sont vérifiés dans le profil Windows documenté. Aucune base de tâches parallèle n’est créée.

### 3. Collaboration facultative entre pairs

Questions et réponses restent liées à la tâche initiale. ChromaSpeechAI utilise des identités de pairs approuvées et TLS. Le contenu reçu est stocké dans une boîte de réception et reste inerte : ce sont des données, pas une permission d’exécuter du code. La divulgation du source exige un consentement explicite.

### 4. Intégrité et examen

Un résultat comporte identité, empreintes et provenance quand le flux existant les fournit. Contributions locales et de pairs restent distinguables. Un SHA-256 identique prouve l’égalité des octets, pas la qualité technique. Le résultat reste non vérifié jusqu’à acceptation par le processus de vérification faisant autorité.

### 5. Publication facultative

Le partage global utilise le flux existant avec vérification, consentement, rôles et acceptation du backend. Les fichiers privés ne deviennent pas automatiquement Shared Network Knowledge. Le logiciel de publication est vérifié localement ; cette version ne prouve pas un service de publication opérationnel en production.

L’accès privé direct du demandeur à un résultat vérifié faisant autorité avant partage global facultatif est reporté. Il ne faut pas le confondre avec la lecture d’un résultat local encore non vérifié.

<!-- page -->
## Confidentialité et confiance

### Trois espaces distincts

**Votre ordinateur :** fichiers, préférences, file, résultats et journaux. Le fournisseur local traite localement les entrées explicitement sélectionnées. L’application ne chiffre pas automatiquement ces données au repos.

**Votre navigateur :** l’application web existante utilise votre Internet Identity. L’appelant réellement authentifié détermine l’accès du propriétaire. Des métadonnées de connexion copiées ne sont pas une session.

**Pairs approuvés et résultats partagés :** l’autorisation concernée contrôle le contenu envoyé. Les connexions peuvent révéler adresses IP et identité des pairs ; ChromaNeural ne promet pas l’anonymat.

Un service traitant des prompts sur un serveur externe exige que les entrées quittent l’ordinateur. Le fournisseur local de ChromaNeural peut les traiter sur place. Collaboration entre pairs et stockage web franchissent toujours une frontière de données. La différence réside dans le contrôle explicite et la séparation, pas dans une promesse de réseau sans divulgation.

### Qu’est-ce qui est vérifié ?

Client Windows et installation propre ont des contrôles automatisés et une acceptation humaine de l’interface. Windows, Linux amd64 et macOS Intel ont des contrôles natifs de compilation/paquet. LAN réel entre deux ordinateurs, WAN direct mobile-vers-domicile et inférence locale réelle sont documentés. Un backend ou une identité synthétique ne constitue pas un test Internet Identity en production.

### Qu’est-ce qui reste non vérifié ?

Internet Identity de bout en bout, admission et migration réelles en production. L’interface macOS manuelle et le cycle complet installation/suppression DEB Linux restent hors acceptation. Le transfert natif de fichiers privés sous l’autorité du propriétaire navigateur n’est pas implémenté. Les performances de matériel spécialisé ne sont pas physiquement vérifiées.

Les paquets ne sont pas signés ; macOS n’est pas notarié. Windows, Linux et macOS sont les plateformes officielles dans ces limites de préversion.

La prise en charge officielle d’Android et d’iOS est reportée.

Consultez les guides Utilisation, Confidentialité et stockage, Installation et Capacités vérifiées.

MCP reste une fonctionnalité post-rc.2 soumise à une décision distincte et n’est pas implémentée ici. Cette documentation n’implique aucune nouvelle modification de la production ou d’Internet Identity.
