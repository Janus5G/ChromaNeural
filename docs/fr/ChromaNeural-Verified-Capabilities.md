# ChromaNeural

[English](../en/ChromaNeural-Verified-Capabilities.md) · [Dansk](../da/ChromaNeural-Verified-Capabilities-DA.md) · [Deutsch](../de/ChromaNeural-Verified-Capabilities.md) · [Français](ChromaNeural-Verified-Capabilities.md) · [日本語](../ja/ChromaNeural-Verified-Capabilities.md) · [简体中文](../zh-CN/ChromaNeural-Verified-Capabilities.md) · [हिन्दी](../hi-IN/ChromaNeural-Verified-Capabilities.md)
## Capacités vérifiées

Documentation ChromaNeural 0.2.21-rc.2 | Candidat non publié | 3 octobre 2026

**État de la documentation rc.2 :** Ce candidat n’a pas été publié. La localisation et l’i18n extensible ont passé la vérification locale ; l’acceptation des compilations et paquets natifs rc.2 reste en attente. Les preuves d’installation, de plateforme, LAN/WAN, d’inférence et de service en production ci-dessous sont historiques et concernent rc.1, sauf mention rc.2 explicite. Les téléchargements rc.1 ne fournissent pas la localisation rc.2.

## Preuves de localisation rc.2

Phases B et C : vérification locale réussie de 303 messages dans sept locales distribuées, sélection persistée, repli anglais, protection des saisies/états, actions modales et contrôles synthétiques de commande/connexion. Capture Tk réelle et acceptation visuelle réussies. Le blocage de la capture chinoise provenait d’interférences de capture du bureau ; l’outil de vérification a utilisé une capture de fenêtre spécifique. Les échecs précédents restent conservés.

L’i18n extensible a également réussi. Un registre de données fournit identifiants, noms et formats numériques. Un huitième catalogue isolé plus une entrée ont validé sélection, persistance, repli, lanceurs Windows et découverte de ressources/paquet ; la locale test a été retirée. Les 476 comparaisons numériques et 2 121 comparaisons de messages ont réussi ; les 331 empreintes sources attendues correspondaient. Ce sont des contrôles locaux, pas une acceptation de paquet natif rc.2, II réel ou production. Aucun rc.2 public n’a été publié.

## Lire les preuves historiques rc.1

**Physique réel :** trafic ou inférence observés sur de vraies machines. **CI native :** un runner du système construit et vérifie le paquet. **Logiciel local :** code/état isolés exécutés ; backend ou session synthétiques ne sont pas la production. **Non vérifié :** preuves insuffisantes. Une limite de l’environnement de test n’est pas automatiquement un défaut produit.

### Windows

Installation propre, intégrité, SDK ICP fourni, CLI, Tk, conservation de l’état et nettoyage sont vérifiés. L’observation humaine finale a montré l’API publique répondant et l’avis que la connexion privée reste au navigateur. Sortie normale du client.

### Linux et macOS

Linux amd64 a été construit et contrôlé sur Ubuntu 24.04 natif : extraction, intégrité, SDK, CLI, Xvfb/Tk. macOS Intel sur macOS 15 natif : intégrité du paquet, SDK, CLI, Tk. Ce sont des résultats de runners, pas une acceptation humaine GUI sur tous les systèmes.

Il y a 18 contrôles par plateforme. La charge Windows CI correspondait aux 1 547 fichiers de la charge locale précédemment acceptée. Les téléchargements finaux ont été vérifiés en SHA-256.

### Inférence locale réelle

Qwen fourni a exécuté l’inférence de fond sous Windows. Ollama 0.34.4 avec qwen2.5-coder:0.5b a tourné sur une autre machine Windows physique. Fournisseur/modèle et empreintes sortie/file/SQLite étaient corrélés. Ni doublons, ni repli, ni points, ni publication. Le plan de contrôle était une fixture isolée ; l’inférence était réelle.

<!-- page -->
## Communication et déroulement

### Deux ordinateurs Windows physiques sur LAN

Deux sens et retour question/réponse vérifiés : identité TLS, égalité des octets, SHA-256, boîte SQLite persistante, redémarrage/reprise, anti-doublons, rejet des inconnus, contenu reçu inerte et arrêt contrôlé.

### WAN direct via Internet et NAT

Un nœud sur une connexion cellulaire distincte a établi TCP direct vers le domicile. ChromaSpeechAI a ensuite validé TLS 1.3, ALPN chromaspeech-prsm-v1, authentification du pair approuvé et charge de 100 000 octets. Octets et SHA-256 identiques. Après redémarrage/reprise, zéro nouveau fragment pour le message déjà reçu. Un pair inconnu a été rejeté avant stockage ; la boîte persistait.

L’initiation indépendante inverse n’a pas pu être vérifiée dans l’environnement disponible. Aucun overlay n’a servi de substitut. La règle temporaire du routeur a été retirée ensuite.

### Fond, ressources et corrélation

La file existante est reliée au cycle de fond du client. Le profil Windows dispose de contrôles ciblés de bail, reprise, pause, arrêt, annulation et redémarrage. Le contrôle couvre ordonnancement CPU, threads et mémoire engagée, sans garantie de RAM physique totale.

La corrélation tâche/pair a utilisé TLS Windows local réel et SQLite ; IA/backend étaient simulés pour ce test. L’installation locale du nœud et la connexion autorisée utilisaient le SDK Windows contre le WASM existant dans PocketIC local. Ce n’est pas l’admission d’un nœud en production.

### Confidentialité, examen et publication

Gardes privées, isolation propriétaire, nettoyage cache/session et intégrité des téléchargements sont vérifiés localement. L’audit global est limité au rôle administrateur existant sans nouveau droit sur le contenu privé. Les tests de publication préservent vérification, consentement, rôles et acceptation du backend. Aucun nouveau déploiement de production n’est prouvé.

<!-- page -->
## Corrections et limites restantes

### Défauts effectivement corrigés

- SDK absent d’une distribution Windows propre : empaquetage du @icp-sdk/core 5.4.0 existant verrouillé et de dix dépendances runtime à la compilation. Ni mise à niveau ni npm côté utilisateur.
- Liaison tâche/message pair manquante : raccordée avec identités, file et boîte existantes.
- Défauts d’endpoints privés et métadonnées d’audit : corrigés localement sans changer Internet Identity, modèle propriétaire, Candid ou schéma stable.
- Découverte des modules PowerShell et chemins temporaires courts/longs corrigés dans l’empaquetage Windows. Échecs CI historiques conservés.

La correction d’export BigInt est une correction de compatibilité, pas un échec runtime universellement reproduit. Les PASS antérieurs sont réutilisés si octets et contrats pertinents restent identiques. Cette mise à jour de présentation n’est pas une nouvelle campagne fonctionnelle.

### Toujours non vérifié ou non livré

- Internet Identity réel de bout en bout, admission et migration en production.
- Interface macOS manuelle et cycle complet DEB Linux installation/suppression.
- Initiation WAN inverse dans l’environnement mobile distinct.
- Fichiers privés natifs sous autorité navigateur et accès privé direct au résultat avant partage global.
- Contribution contrôlée Ollama/Linux/macOS/GPU ; partage général désactivé.
- Paquets non signés, macOS non notarié ; limites d’icônes documentées séparément.

La prise en charge officielle d’Android et d’iOS est reportée.

### Matériel et reproductibilité

Il s’agit de logiciel. LAN/WAN et inférence réels étayent les machines et connexions testées. Simulations, backend local et modèles matériels ne prouvent pas les performances physiques optiques/GPU/spécialisées.

Les workflows natifs utilisent checkout propre, Actions/dépendances fixées, verrou npm et ressources runtime vérifiées par empreinte. Systèmes runners et métadonnées exécutables peuvent modifier les hashes des paquets ; aucune identité binaire universelle n’est revendiquée. VERIFICATION.md et NATIVE_BUILD_EVIDENCE.json identifient les builds acceptés. Empreintes dans docs/DOWNLOADS.md et SHA256SUMS.txt de la publication.

MCP reste une fonctionnalité post-rc.2 soumise à une décision distincte et n’est pas implémentée ici. Cette documentation n’implique aucune nouvelle modification de la production ou d’Internet Identity.
