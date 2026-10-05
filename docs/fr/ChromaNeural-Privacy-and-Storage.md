# ChromaNeural

[English](../en/ChromaNeural-Privacy-and-Storage.md) · [Dansk](../da/ChromaNeural-Privacy-and-Storage-DA.md) · [Deutsch](../de/ChromaNeural-Privacy-and-Storage.md) · [Français](ChromaNeural-Privacy-and-Storage.md) · [日本語](../ja/ChromaNeural-Privacy-and-Storage.md) · [简体中文](../zh-CN/ChromaNeural-Privacy-and-Storage.md) · [हिन्दी](../hi-IN/ChromaNeural-Privacy-and-Storage.md)
## Confidentialité et stockage

Documentation ChromaNeural 0.2.21-rc.2 | Candidat non publié | 3 octobre 2026

**État de la documentation rc.2 :** Ce candidat n’a pas été publié. La localisation et l’i18n extensible ont passé la vérification locale ; l’acceptation des compilations et paquets natifs rc.2 reste en attente. Les preuves d’installation, de plateforme, LAN/WAN, d’inférence et de service en production ci-dessous sont historiques et concernent rc.1, sauf mention rc.2 explicite. Les téléchargements rc.1 ne fournissent pas la localisation rc.2.

## Trois frontières de données

**Client local :** fichiers, tâches locales, préférences et journaux résident sur votre ordinateur. Vous choisissez espace de travail et actions. Choisir un dossier ne le téléverse pas.

**Navigateur et Internet Identity :** l’accès privé web utilise l’application existante et l’appelant réellement authentifié. Un Principal dans du JSON identifie, mais ne prouve pas l’autorité du propriétaire. Le nœud ne doit pas emprunter la session humaine.

**Pairs et connaissances partagées :** des contenus autorisés séparément peuvent aller aux pairs approuvés. La publication globale impose vérification, consentement, rôles et backend. Le privé ne devient pas automatiquement Shared Network Knowledge.

Cette séparation ne change ni Internet Identity, ni modèle de stockage web, ni droits existants. Elle ne signifie ni chiffrement au repos ni anonymat réseau.

### Comparaison avec le traitement centralisé

Un service d’IA central traitant un prompt sur serveur externe fait sortir l’entrée de l’ordinateur. L’inférence locale de ChromaNeural peut traiter sur place les entrées choisies. Si vous choisissez la collaboration réseau, les contenus approuvés sont envoyés. Le stockage privé web conserve son modèle d’accès du propriétaire.

ChromaNeural ne prétend pas que les autres IA manquent toutes de confidentialité, ni que le stockage local suffit. Système, sauvegardes, fournisseur choisi et contenus approuvés comptent toujours.

### Aucun transfert implicite d’autorité

Le profil API contient des champs publics et éventuellement un Principal, pas un jeton de connexion. Le nœud a une identité séparée à un chemin local choisi. Son enregistrement ne l’admet pas automatiquement. Les préférences de ressources n’ouvrent pas les objets privés.

<!-- page -->
## Emplacement des données

### Répertoire d’état par défaut

Windows :
```
%LOCALAPPDATA%\ChromaNeural\client
```

Linux et macOS :
```
${XDG_STATE_HOME:-$HOME/.local/state}/chroma-neural/client
```

macOS utilise la même convention XDG/repli que Linux, pas automatiquement Library/Application Support. --state-dir explicite est prioritaire ; sinon CHROMA_STATE_DIR peut choisir un autre répertoire. Réutilisez cette sélection pour retrouver le même profil local.

### Fichiers d’état du client

- **preferences.json :** thème, participation, CPU/threads/mémoire, repos/batterie et chemin de configuration du nœud. Aucune session II.
- **ui-language.json (rc.2) :** uniquement version 1 et identifiant de locale enregistré, après sélection GUI explicite dans ce même répertoire. Aucune session II ni modification de preferences.json. Valeur absente/invalide/trop grande/non prise en charge : anglais sans réécriture destructive. Une sauvegarde explicite ultérieure conserve l’original invalide ; l’échec conserve la langue courante. --language n’est pas persisté.
- **api-connection-v1.json :** profil API enregistré. Un Principal peut identifier une personne ; des métadonnées publiques ne sont pas anonymes.
- **work-queue.db :** file SQLite existante et état de publication associé. Les tâches peuvent contenir source, instructions, résultats et références. SQLite peut créer des fichiers -wal et -shm pendant l’utilisation.
- **balance-cache.json :** état comptable précédemment récupéré. Un cache ne crée pas une attribution de points faisant autorité.
- **client.log :** journal tournant, jusqu’à 1 MiB par fichier et trois sauvegardes. Les traces peuvent exposer des chemins locaux.

La lecture conserve les fichiers de paramètres/profils invalides. Une sauvegarde explicite ultérieure peut garder une copie datée. Ne les supprimez pas automatiquement pour dépanner.

### Autres emplacements explicitement choisis

Les fichiers de travail restent dans l’espace choisi. Configuration et identité du nœud utilisent les répertoires d’installation choisis ; l’identité peut contenir private_key.pem et public_key.json. Boîtes de réception et files CLI avancées utilisent des chemins de base explicites, pas nécessairement le répertoire par défaut.

Ne publiez jamais private_key.pem, répertoires d’identité, bases de file ou journaux non expurgés. Ce guide ne les demande pas.

<!-- page -->
## Chemins et fichiers privés

L’espace de travail est un dossier local choisi explicitement. Un chemin ordinaire est un chemin système, pas un transfert de propriété. L’espace actif de l’interface est un état de session ; ce flux ne fournit pas de service général de synchronisation des dossiers récents.

Des chemins peuvent néanmoins persister ailleurs : preferences.json peut référencer une configuration de nœud, et les données de collaboration/publication une boîte de réception. Les journaux peuvent contenir des chemins. Fermer la fenêtre d’un espace ne supprime donc pas toutes les références.

L’adaptateur local existant traite des fichiers texte nommés. Il vérifie noms, liens symboliques/points de réanalyse et changements entre lecture et écriture. La sauvegarde utilise fichier temporaire et remplacement atomique avec contrôles d’intégrité existants. Ce n’est pas un client de disque cloud général.

Ces mécanismes ne chiffrent pas les données. Protégez compte et disque, et sauvegardez selon vos besoins. Quittez avant de copier SQLite ; une base WAL active n’est pas un fichier isolé quelconque. Déplacer les programmes ne déplace pas automatiquement espace, identité ou état.

### Que reçoit un fournisseur ou un pair ?

L’IA locale utilise l’entrée choisie et approuvée. Le modèle de tâche peut persister entrée et instructions dans la file. La divulgation à un pair demande une autorisation distincte. Un transport approuvé ne rend pas inoffensifs chemins privés, secrets ou données personnelles inclus dans le texte.

TLS protège la connexion authentifiée. Il ne cache pas les IP aux réseaux des extrémités et ne garantit pas la sécurité d’un ordinateur compromis.

<!-- page -->
## Sessions navigateur et accès privé

La connexion utilise l’application web existante et Internet Identity. Le client natif ne reprend pas la session II. **Kontrollér forbindelse** vérifie anonymement l’API publique ; son succès ne dit rien des données privées ni de la validité de la session navigateur.

La correction navigateur vérifiée localement efface cache/formulaires privés à la déconnexion et au changement d’utilisateur, gère l’expiration et vérifie propriétaire et SHA-256 avant téléchargement. Les corrections backend restreignent accès privé anonyme et métadonnées d’audit globales. Ce sont des preuves locales. Cette préversion n’a pas déployé ces changements ; le parcours II réel de bout en bout reste NON VÉRIFIÉ.

Déconnectez-vous par le flux existant du navigateur. Fermer le bureau ou oublier le profil API ne déconnecte pas le navigateur et ne révoque pas à lui seul les autorisations. Octroi/révocation utilisent leurs interfaces autorisées ; aucun nouveau type de droit n’est introduit.

### Accès natif aux fichiers privés

**Private II storage** est informatif. Le canal autorisé navigateur/natif manquant n’est pas implémenté. Le nœud ne peut écrire comme propriétaire humain ; un droit de lecture ne vaut pas écriture. Aucun stockage alternatif ne contourne cette frontière.

### Résultats privés et connaissances globales

Propositions locales et réponses de pairs ne sont pas encore des connaissances vérifiées. Vérification, consentement, rôles et acceptation du backend régissent la publication facultative. L’égalité d’intégrité n’approuve ni qualité ni publication.

Le téléchargement privé direct par le demandeur d’un résultat vérifié faisant autorité avant partage global facultatif est reporté. Aucun accès via un canal propriétaire non implémenté n’est promis.

### Erreurs et divulgation suspectée

Arrêtez l’action, conservez les preuves en privé et suivez SECURITY.md. Fournissez description expurgée et version, pas de clés, sessions ou bases privées. Un SHA-256 différent prouve des octets différents ; fichier ou empreinte manquants sont d’autres erreurs, pas une falsification prouvée.

MCP reste une fonctionnalité post-rc.2 soumise à une décision distincte et n’est pas implémentée ici. Cette documentation n’implique aucune nouvelle modification de la production ou d’Internet Identity.
