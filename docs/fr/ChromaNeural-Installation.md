# ChromaNeural

[English](../en/ChromaNeural-Installation.md) · [Dansk](../da/ChromaNeural-Installation-DA.md) · [Deutsch](../de/ChromaNeural-Installation.md) · [Français](ChromaNeural-Installation.md) · [日本語](../ja/ChromaNeural-Installation.md) · [简体中文](../zh-CN/ChromaNeural-Installation.md) · [हिन्दी](../hi-IN/ChromaNeural-Installation.md)
## Installation

Documentation ChromaNeural 0.2.21-rc.2 | Candidat non publié | 3 octobre 2026

**État de la documentation rc.2 :** Ce candidat n’a pas été publié. La localisation et l’i18n extensible ont passé la vérification locale ; l’acceptation des compilations et paquets natifs rc.2 reste en attente. Les preuves d’installation, de plateforme, LAN/WAN, d’inférence et de service en production ci-dessous sont historiques et concernent rc.1, sauf mention rc.2 explicite. Les téléchargements rc.1 ne fournissent pas la localisation rc.2.

## Référence d’installation historique rc.1

Aucun paquet rc.2 public n’est encore disponible. Les noms et commandes suivants restent volontairement des exemples rc.1 et n’installent ni sélecteur de langue ni registre. Pour un candidat rc.2 local déjà préparé, --language choisit la langue du lancement seulement ; Windows accepte -Language. La sélection GUI persiste. Ne renommez pas un paquet rc.1 et ne remplacez pas l’URL par un téléchargement rc.2 non vérifié.

## Avant installation

Téléchargez depuis la publication officielle :

../../RELEASE_NOTES.md

Choisissez plateforme et architecture exactes. Paquets non signés, macOS non notarié : le système peut avertir ou bloquer. Ne désactivez pas globalement la sécurité. Vérifiez origine et empreinte avant ouverture.

- Windows x64 : ChromaNeural-0.2.21-rc.1-windows-x64.exe
- Linux amd64 : chromaneural_0.2.21.rc.1_amd64.deb
- macOS Intel x86_64 : ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
- Instantané source : ChromaNeural-0.2.21-rc.1-source.zip
- Empreintes : SHA256SUMS.txt

GitHub a normalisé le nom DEB de ~rc.1 en .rc.1. Octets et SHA-256 sont inchangés ; la version Debian interne garde ~rc.1.

### Vérifier SHA-256

Dans le répertoire du paquet téléchargé, exécutez la commande adaptée.

Windows PowerShell :
```
Get-FileHash -Algorithm SHA256 -LiteralPath '.\ChromaNeural-0.2.21-rc.1-windows-x64.exe'
```

Linux :
```
sha256sum chromaneural_0.2.21.rc.1_amd64.deb
```

macOS :
```
shasum -a 256 ChromaNeural-0.2.21-rc.1-macos-x86_64.zip
```

Comparez les 64 caractères à la ligne du nom exact dans SHA256SUMS.txt. Arrêtez en cas de différence. L’empreinte vérifie les octets, pas indépendamment l’identité de l’éditeur. Les cinq empreintes publiées figurent aussi dans docs/DOWNLOADS.md.

<!-- page -->
## Windows x64

### Prérequis

Python 3.14 avec Tk et lanceurs py/pyw, plus Node.js 24. L’EXE est un installateur hors ligne par utilisateur, pas un runtime Python/Node totalement embarqué. Prévoyez environ 2 GB libres pour extraction et installation.

### Étapes

1. Vérifiez l’EXE comme indiqué.
2. Ouvrez et confirmez après examen des avertissements système.
3. Répertoire versionné des programmes :
```
%LOCALAPPDATA%\Programs\ChromaNeural\0.2.21-rc.1
```
4. Lancez Start-ChromaNeural.ps1 depuis ce dossier :
```
& "$env:LOCALAPPDATA\Programs\ChromaNeural\0.2.21-rc.1\Start-ChromaNeural.ps1"
```
5. Enregistrez les ressources au premier lancement. Connexion et authentification permet un contrôle API public facultatif.

Journal : %TEMP%\ChromaNeural-install.log. Les destinations existantes sont refusées ; pas de mise à niveau automatique sur place. Ni participation automatique ni inscription au démarrage système. Cette RC ne crée pas automatiquement de raccourci bureau.

SDK ICP et dépendances verrouillées sont inclus. npm ci n’est pas requis ; ne pointez pas NODE_PATH vers un ancien environnement de développement.

### Suppression et état utilisateur

Quittez complètement. Supprimer seulement le dossier versionné enlève les programmes. L’état sous %LOCALAPPDATA%\ChromaNeural\client, les espaces et identités séparées doivent être conservés ou traités séparément selon votre choix explicite. Aucun désinstallateur automatique n’est inclus.

<!-- page -->
## Linux amd64

Le profil natif vérifié est Ubuntu 24.04 amd64, pas toutes les distributions/versions. WSL ne remplace pas la vérification native Linux.

Requis : Python 3.11+, Tk, cryptography de la distribution, Node.js 20+, libgomp1. Utilisez le gestionnaire de paquets pour les dépendances. Depuis le dossier de téléchargement :
```
sudo apt install ./chromaneural_0.2.21.rc.1_amd64.deb
```

Lancez via le menu ou :
```
chromaneural
```

Programmes : /opt/chromaneural ; lanceur : /usr/bin/chromaneural ; métadonnées : /usr/share/applications/chromaneural.desktop. Aucun téléchargement npm après installation ni migration automatique d’état utilisateur.

Compilation native, extraction, intégrité, SDK, CLI et Xvfb/Tk sont vérifiés. Le cycle dpkg complet installation/suppression ne l’est pas. L’entrée desktop publiée manque d’icône spécifique ; le lancement reste possible.

## macOS Intel x86_64

macOS 15+, Python 3.14 avec Tk fonctionnel et Node.js 24 sont requis. Utilisez le même Python pour les dépendances crypto fixées. Depuis la racine de l’instantané source accepté :
```
python3 -m pip install --require-hashes -r packaging/requirements-runtime.txt
```

Versions verrouillées : cryptography 46.0.5, cffi 2.1.1, pycparser 3.0. Ce sont des prérequis runtime, pas une demande d’identifiants II.

Extrayez la ZIP, déplacez ChromaNeural.app dans Applications et ouvrez après vérification d’origine et avertissements. Intel seulement ; Universal 2, Apple Silicon et Rosetta ne sont pas des profils acceptés ici.

Compilation native, intégrité, SDK, CLI et Tk sont vérifiés ; interface macOS manuelle non vérifiée. Paquet non signé, non notarié, sans icône spécifique de bundle. Aucun runtime Qwen/llama.cpp fourni sur macOS. L’adaptateur Ollama local explicite exige un modèle installé séparément ; contribution contrôlée de fond non prise en charge.

<!-- page -->
## Premier lancement et suite

![Ressources du véritable client Windows ; décorations variables selon le système.](../images/chroma-neural-resources.png)

Choisissez et enregistrez. La vue d’ensemble n’affiche que des valeurs confirmées ; un tiret n’est pas une promesse de gain. Partage général désactivé. **Afslut ChromaNeural** ferme complètement.

En cas d’échec, contrôlez d’abord prérequis, paquet et architecture. Préservez l’état. Ne réinitialisez pas les identités et ne publiez pas de données privées. Voir Utilisation et Confidentialité et stockage.

L’installation ne change ni Internet Identity, ni backend de production, ni session navigateur. L’API publique a été atteinte sous Windows. II réel de bout en bout, admission et migration en production restent non vérifiés.

La prise en charge officielle d’Android et d’iOS est reportée.

La documentation en ligne peut être plus récente que les binaires RC et ZIP source immuables. Les fichiers publiés ne sont pas remplacés uniquement pour documentation ou icônes. Voir docs/BRANDING.md.

MCP reste une fonctionnalité post-rc.2 soumise à une décision distincte et n’est pas implémentée ici. Cette documentation n’implique aucune nouvelle modification de la production ou d’Internet Identity.
