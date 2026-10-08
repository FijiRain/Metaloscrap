# 🎸 Metaloscrap

**Metaloscrap** est un outil d'automatisation qui surveille le webzine [Metalorgie](https://www.metalorgie.com/news), détecte chaque semaine le dernier post *"Les sorties de la semaine"*, filtre les albums selon vos genres favoris, et génère automatiquement une playlist Spotify contenant l'intégralité des titres de chaque album sélectionné.

L'outil fonctionne à la fois :
- En **local** via la ligne de commande (avec un mode simulation `--dry-run`).
- En **automatisation complète** via **GitHub Actions** (déclenchement chaque vendredi à 18h UTC + exécution manuelle).

---

## 📋 Table des matières

1. [Fonctionnalités](#-fonctionnalités)
2. [Prérequis](#-prérequis)
3. [Configuration initiale de Spotify (Une seule fois)](#-configuration-initiale-de-spotify)
4. [Personnalisation des genres](#-personnalisation-des-genres)
5. [Utilisation en local](#-utilisation-en-local)
6. [Automatisation avec GitHub Actions](#-automatisation-avec-github-actions)
7. [Tests unitaires](#-tests-unitaires)

---

## ✨ Fonctionnalités

- **Scraping direct & léger :** Extraction propre via requêtes HTTP et parsing HTML (`lxml`), sans navigateur lourd (Playwright/Selenium non requis).
- **Filtrage souple par genres :** Mots-clés insensibles à la casse, gestion des accents et des sous-genres (`Noise Rock`, `mathcore`, `experimental`, `screamo`, `Sludge`, etc.).
- **Ajout d'albums complets :** Récupération de l'ensemble des pistes de chaque album retenu.
- **Playlists horodatées & Idempotence :** Création d'une playlist par semaine (ex. `Metaloscrap - Semaine 41 (2026)`) avec vérification préalable pour éviter les doublons.
- **Reporting détaillé :** Récapitulatif Markdown en console et dans le *GitHub Actions Step Summary* avec la liste des albums ajoutés et les sorties introuvables (ex. exclusivités Bandcamp).
- **Gestionnaire uv :** Gestion des dépendances ultra-rapide et reproductible avec `uv`.

---

## 🛠️ Prérequis

- **Python 3.10+**
- **uv** : gestionnaire de paquets rapide ([Installer uv](https://docs.astral.sh/uv/getting-started/installation/)) :
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

---

## 🔑 Configuration initiale de Spotify

Pour que Metaloscrap puisse créer des playlists sur votre compte sans vous demander de mot de passe à chaque fois, l'outil utilise le flux OAuth 2.0 avec *Refresh Token*.

### 1. Créer une application Spotify Developer
1. Rendez-vous sur le [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) et connectez-vous.
2. Cliquez sur **Create App**.
3. Renseignez :
   - **App name :** `Metaloscrap`
   - **App description :** `Scraping Metalorgie pour sorties d'albums`
   - **Redirect URI :** `http://127.0.0.1:8888/callback` *(très important, Spotify refuse désormais `localhost` !)*
   - Cochez les conditions d'utilisation et validez (**Save**).
4. Sur la page de votre application, allez dans **Settings** et notez votre **Client ID** et votre **Client Secret**.

### 2. Générer le Refresh Token (Script interactif)
Lancez simplement l'assistant interactif fourni :

```bash
uv run python auth_setup.py
```

Le script va :
1. Vous demander votre `Client ID` et `Client Secret`.
2. Ouvrir votre navigateur pour que vous autorisiez Metaloscrap.
3. Récupérer le `SPOTIFY_REFRESH_TOKEN` et créer automatiquement votre fichier local `.env`.

---

## 🎛️ Personnalisation des genres

Éditez le fichier `genres.json` à la racine pour définir les genres que vous souhaitez surveiller.

Exemple actuel :
```json
[
  "Noise",
  "Noise Rock",
  "mathcore",
  "experimental",
  "screamo"
]
```

La détection est souple : `"Noise"` trouvera les albums tagués `"Noise"`, `"Noise Rock"` ou `"Noise / Punk"`.

---

## 💻 Utilisation en local

### Tester sans toucher à Spotify (Simulation `--dry-run`)
Pour vérifier ce que Metaloscrap détecterait sur Metalorgie sans modifier votre compte Spotify :

```bash
uv run python metaloscrap.py --dry-run
```

### Exécution réelle
Pour créer la playlist et ajouter les albums de la semaine :

```bash
uv run python metaloscrap.py
```

Options disponibles :
- `--dry-run` : Analyse le site et filtre les genres sans appel Spotify.
- `--config mon_fichier.json` : Utilise une configuration de genres alternative.
- `--force` : Recrée la playlist même si une playlist portant ce nom existe déjà.
- `--public` : Rend la playlist publique (privée par défaut).

---

## 🤖 Automatisation avec GitHub Actions

Le projet inclut un workflow planifié dans [`.github/workflows/weekly_playlist.yml`](.github/workflows/weekly_playlist.yml) qui s'exécute automatiquement **tous les vendredis à 18h00 UTC**.

### Configuration sur votre dépôt GitHub :
1. Poussez votre projet sur GitHub :
   ```bash
   git add .
   git commit -m "feat: setup metaloscrap with uv and spotify integration"
   git push origin main
   ```
2. Sur votre dépôt GitHub, allez dans :
   **Settings > Secrets and variables > Actions > New repository secret**
3. Ajoutez les 3 secrets suivants (obtenus lors de l'étape `auth_setup.py`) :
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `SPOTIFY_REFRESH_TOKEN`
4. C'est tout ! Chaque vendredi soir, votre playlist sera automatiquement créée et le résumé apparaîtra dans l'onglet **Actions** de GitHub. Vous pouvez également déclencher l'action manuellement à tout moment via le bouton **Run workflow**.

---

## 🧪 Tests unitaires

Pour exécuter l'ensemble de la suite de tests :

```bash
uv run python -m unittest discover -s tests
```
