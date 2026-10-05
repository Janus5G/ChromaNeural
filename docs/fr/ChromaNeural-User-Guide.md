# ChromaNeural

[English](../en/ChromaNeural-User-Guide.md) · [Dansk](../da/ChromaNeural-User-Guide-DA.md) · [Deutsch](../de/ChromaNeural-User-Guide.md) · [Français](ChromaNeural-User-Guide.md) · [日本語](../ja/ChromaNeural-User-Guide.md) · [简体中文](../zh-CN/ChromaNeural-User-Guide.md) · [हिन्दी](../hi-IN/ChromaNeural-User-Guide.md)
## Guide utilisateur

Documentation ChromaNeural 0.2.21-rc.2 | Candidat non publié | 3 octobre 2026

**État de la documentation rc.2 :** Ce candidat n’a pas été publié. La localisation et l’i18n extensible ont passé la vérification locale ; l’acceptation des compilations et paquets natifs rc.2 reste en attente. Les preuves d’installation, de plateforme, LAN/WAN, d’inférence et de service en production ci-dessous sont historiques et concernent rc.1, sauf mention rc.2 explicite. Les téléchargements rc.1 ne fournissent pas la localisation rc.2.

## 1. Installer et démarrer

Téléchargez le paquet de votre plateforme depuis la publication GitHub officielle et comparez SHA-256 à la liste. Installez les prérequis du guide Installation. Le SDK ICP verrouillé est inclus ; ni npm ni ancien environnement de développement ne sont nécessaires.

Sous Windows, lancez Start-ChromaNeural.ps1 depuis le dossier d’installation utilisateur versionné. Sous Linux, utilisez le menu d’applications ou chromaneural. Sous macOS, ouvrez ChromaNeural.app après installation des prérequis. Les paquets sont non signés ; ne désactivez pas globalement la sécurité du système.

Le premier lancement affiche les préférences de ressources : choisissez et enregistrez. Cela n’admet pas automatiquement le client sur un réseau de production. Les exemples montrent une participation arrêtée sans compte ni données privées.

![Présentation après enregistrement des préférences, participation arrêtée.](../images/chroma-neural-overview.png)

Ces captures rc.1 conservées sont en danois, sans sélecteur de langue rc.2. **Oversigt** signifie Vue d’ensemble ; **Ressourcer**, Ressources ; **Aktivitet**, Activité ; **Login & forbindelse**, Connexion et authentification. Les étapes conservent ces anciens libellés avec leur traduction. rc.2 démarre en anglais sauf choix explicite d’une autre langue.

Un tiret signifie qu’aucune valeur confirmée n’est disponible, pas un solde nul ni un gain estimé. Changez de page avec la navigation à gauche.

## Langue du client rc.2

Un seul client prend en charge English, Dansk, Deutsch, Français, 日本語, 简体中文 et हिन्दी. L’anglais est la langue par défaut et de repli, indépendamment du système. Le sélecteur latéral change immédiatement les textes de l’application. Les saisies, le code source, le JSON de connexion et l’état de participation sont conservés ; changer de langue ne lance ni worker supplémentaire ni contrôle réseau. Les boîtes de sélection de fichiers du système gardent sa langue.

Un choix explicite dans l’interface enregistre seulement la version et la locale dans `ui-language.json`, à côté de `preferences.json`, sans changer son schéma ni créer un second répertoire d’état. Le choix revient au prochain démarrage. Une préférence absente, invalide, trop volumineuse ou non prise en charge entraîne un repli sur l’anglais sans réécrire l’original. Un enregistrement explicite ultérieur conserve un original invalide ; un échec de sauvegarde conserve la langue courante.

L’argument CLI facultatif `--language` remplace la langue pour ce lancement sans l’enregistrer. Les lanceurs Windows transmettent `-Language`. Les identifiants proviennent de `client/locale-registry.json` ; l’ensemble initial est `en`, `da`, `de`, `fr`, `ja`, `zh-CN`, `hi-IN`. Une future langue demande un catalogue avec les mêmes clés de messages et une entrée de registre contenant nom et métadonnées de format numérique. La huitième locale temporaire de test n’est pas distribuée.

Dans le client rc.2, les libellés correspondants dans la langue de ce guide sont :

| Libellé de la capture historique | Libellé rc.2 en français |
|---|---|
| Oversigt | Vue d’ensemble |
| Ressourcer | Ressources |
| Aktivitet | Activité |
| Login & forbindelse | Connexion et accès |
| Udviklerværktøjer  ↗ | Outils de développement  ↗ |
| Afslut ChromaNeural | Quitter ChromaNeural |
| Gem ændringer | Enregistrer les modifications |
| Gem og fortsæt | Enregistrer et continuer |
| Log ind med Internet Identity | Se connecter avec Internet Identity |
| Gem forbindelsesdata | Enregistrer la connexion |
| Kontrollér forbindelse | Vérifier la connexion |
| Backend svarer · offentligt API nået<br>Privat login er fortsat i browseren | Le backend répond · API publique atteinte<br>La connexion privée reste dans le navigateur |
| Lokal AI | IA locale |
| Privat II-lagring | Stockage II privé |

<!-- page -->
## 2. Ressources et participation

![Préférences réelles ; la contribution CPU n’est pas activée dans cet exemple.](../images/chroma-neural-resources.png)

1. Ouvrez **Ressourcer** (Ressources).
2. Choisissez le maximum de threads d’inférence et la préférence mémoire.
3. Choisissez le calcul seulement au repos et la pause sur batterie.
4. Réglez le comportement de la zone de notification si la plateforme le permet.
5. Sélectionnez **Gem ændringer** (Enregistrer les modifications), ou **Gem og fortsæt** (Enregistrer et continuer) au premier lancement. Revenez par **Oversigt**.

Un réglage est une limite, pas une réservation de matériel. Le profil Windows avec CPU fourni applique ordonnancement CPU, threads et mémoire engagée. La RAM physique totale/RSS n’est pas garantie. Les contributions contrôlées Ollama, Linux, macOS et GPU ne sont pas prises en charge et ne doivent pas être annoncées comme des profils contraints.

Le partage général reste désactivé. Démarrer ou suspendre ne contourne ni autorisations de tâches, ni admission du nœud, ni contrôles de ressources. Du matériel installé ou inutilisé ne rapporte pas de points.

<!-- page -->
## 3. Authentification et connexion

![Connexion sans profil chargé ; authentification navigateur et contrôle API sont séparés.](../images/chroma-neural-connection.png)

1. Ouvrez **Login & forbindelse** (Connexion et authentification).
2. **Log ind med Internet Identity** ouvre l’application web existante. Utilisez votre identité existante ; ne partagez jamais session ou récupération.
3. Copiez le profil API de l’application web, collez-le dans le client, puis **Gem forbindelsesdata** (Enregistrer les données de connexion).
4. **Kontrollér forbindelse** (Vérifier la connexion) contrôle l’API publique sans transférer votre session privée.
5. Le succès affiche **Backend svarer · offentligt API nået** et **Privat login er fortsat i browseren** : le backend répond, l’API publique est atteinte, la connexion privée reste dans le navigateur.

Ce message a été observé lors de l’acceptation historique Windows rc.1. Il prouve la joignabilité de l’API publique, pas l’accès privé, l’admission ou la migration en production. Ce guide ne demande aucun déploiement ni changement de backend.

En cas d’échec, vérifiez accès Internet, profil et prérequis Python/Node. Partagez une description expurgée seulement ; les journaux peuvent contenir des chemins locaux. Ne commencez pas par réinitialiser les identités ou supprimer l’état.

Le parcours II réel de bout en bout reste NON VÉRIFIÉ. La sortie du client ne prouve pas le déploiement des corrections locales de contrôle d’accès sur l’application web publique.

<!-- page -->
## 4. Activité, pause et sortie

![Activité avec un véritable enregistrement local des paramètres.](../images/chroma-neural-activity.png)

Activité montre les événements enregistrés : sauvegarde ou état d’une action. Un événement seul ne prouve ni qualité d’IA vérifiée, ni publication, ni points.

Le worker pris en charge doit respecter pause et arrêt. Les tâches approuvées conservent leur identité dans la file après redémarrage contrôlé. Le contenu des pairs reste inerte.

**Afslut ChromaNeural** (Quitter ChromaNeural) ferme complètement. Le bouton de fermeture peut seulement masquer le client si le mode zone de notification est activé et pris en charge. Quittez avant de sauvegarder ou déplacer l’état.

<!-- page -->
## 5. IA locale et opérations avancées

L’IA locale existante se trouve sous **Udviklerværktøjer** (Outils de développement). Ouvrez ou enregistrez le fichier texte concerné. Choisissez **Local AI**, fournisseur/modèle local pris en charge et instruction, puis autorisez l’entrée exacte. Examinez la proposition avant acceptation et sauvegarde : elle ne remplace pas automatiquement le fichier.

CPU/Qwen fourni est disponible sur Windows/Linux. Un modèle Ollama local installé se choisit explicitement. macOS ne contient pas de runtime Qwen. Aucun repli automatique vers un autre fournisseur. L’IA locale manuelle est distincte du profil réseau de ressources contrôlées.

File et pairs sont des fonctions CLI avancées de cette RC : queue-ai, result, task-question, task-accept, task-reply, task-collect, task-status. Consultez --help et choisissez explicitement une configuration locale. Ce n’est pas un enrôlement automatique en production.

## 6. Fichiers privés et résultats

Travaillez uniquement dans les dossiers choisis. **Private II storage** est informatif : aucun transfert privé. Les données du propriétaire navigateur et les fichiers du bureau ne sont pas encore reliés par un canal autorisé.

Un résultat local se révise comme proposition. Une réponse de pair approuvée n’est pas automatiquement vérifiée même avec SHA-256 identique. La publication globale exige vérification, consentement, rôles et acceptation du backend. Télécharger ou examiner n’accorde pas de ChromaPoints.

Les captures conservent le client historique rc.1. Le pied 0.2.5 est un libellé de composant interne ; la distribution documentée est 0.2.21-rc.1.

MCP reste une fonctionnalité post-rc.2 soumise à une décision distincte et n’est pas implémentée ici. Cette documentation n’implique aucune nouvelle modification de la production ou d’Internet Identity.
