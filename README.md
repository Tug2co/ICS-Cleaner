# ICS Cleaner — Nettoyeur d'agenda iCalendar

**But** : petit service web qui importe un calendrier `.ics` depuis une URL, nettoie/modifie les `SUMMARY` des événements (par ex. retirer un code de type `N5* - ` ou supprimer certains événements), puis renvoie un `.ics` nettoyé prêt à télécharger ou à s'abonner (ex : via Google Calendar).

Ce README explique précisément : le fonctionnement, le code, les fichiers, et **pas à pas** comment déployer sur GitHub + Render (gratuit) ainsi que des notes de sécurité et de personnalisation.

---

## Contenu du dépôt

* `app.py` — l'application Flask principale (interface HTML + endpoint `/clean_ics`).
* `requirements.txt` — dépendances Python.
* `Procfile` — instruction pour Gunicorn (déploiement Render).
* `.gitignore` — fichiers à ignorer (optionnel).

---

## Fonctionnalités

* Télécharge un `.ics` depuis une URL fournie.
* Remplace ou nettoie le `SUMMARY` des événements selon une regex configurable.
* Filtre (supprime) des événements dont les titres correspondent à une chaîne (ex. `SPORT DU JEUDI activités différées`).
* Renvoie un fichier `.ics` téléchargeable.
* Interface web simple pour coller l'URL et télécharger le `.ics` nettoyé.

---

## Prérequis locaux

* Python 3.9+ (ou 3.8+)
* `pip`
* (Optionnel) Compte GitHub + compte Render pour déploiement gratuit

---

## Installation & exécution locale

1. Cloner ou créer le dossier du projet.
2. Créer un environnement virtuel (recommandé) :

```bash
python -m venv venv
source venv/bin/activate   # macOS / Linux
venv\Scripts\activate     # Windows
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Lancer l'application :

```bash
python app.py
```

5. Ouvrir ton navigateur :

```
http://localhost:5000/
```

Colle l'URL ICS dans le formulaire et clique sur **Nettoyer et télécharger**.

---

## Contenu principal : `app.py` (explication)

L'application est volontairement compacte. Points importants :

* **Interface simple** (`GET /`) pour coller l'URL.
* **Endpoint** `POST /clean_ics` (le code accepte aussi GET) : traite l'URL et renvoie le `.ics` filtré.
* Utilise la librairie `requests` pour télécharger le flux ICS. Un `User-Agent` navigateur est ajouté pour éviter les blocages par certains serveurs. La vérification SSL est désactivée (`verify=False`) pour améliorer la compatibilité avec certains ENT — voir notes sécurité.
* Utilise la librairie `ics` pour parser et générer l'ICS.

### Lignes clés à personnaliser

* **Suppression des codes N5** (au début du titre) :

```python
clean_name = re.sub(r"^\s*N5\S*\s*-\s*", "", ev.name)
```

Cette ligne supprime un mot commençant par `N5` (ex : `N5A123 - `) au début du SUMMARY.

* **Suppression d'événements spécifiques** :

```python
if ev.name and "sport du jeudi activités différées" in ev.name.lower():
    continue
```

Cette condition ignore complètement l'événement si son titre contient la chaîne (insensible à la casse).

---

## `requirements.txt`

Contenu minimal :

```
flask
ics
requests
```

---

## `Procfile`

Contenu :

```
web: gunicorn app:app
```

(cette ligne demande à Render d'exécuter Gunicorn comme serveur de production)

---

## Déploiement sur Render (pas à pas)

### 1) Préparer le dépôt GitHub

* Initialiser git et pousser le dépôt :

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<TON_UTILISATEUR>/<NOM_DU_DEPOT>.git
git push -u origin main
```

### 2) Créer un compte Render

1. Va sur [https://render.com](https://render.com) et inscris-toi (tu peux te connecter via GitHub).
2. Cliquer sur **New + → Web Service**.
3. Choisir le dépôt que tu viens de pousser.
4. Paramètres recommandés :

   * Branch: `main`
   * Region: `Oregon` ou `Frankfurt` (choisir Europe si proche de toi)
   * Build Command: `pip install -r requirements.txt`
   * Start Command: `gunicorn app:app`
5. Créer et attendre le build.

Après build, Render affichera une URL publique (ex : `https://ics-cleaner.onrender.com`).

### 3) Tester en ligne

* Ouvrir l'URL racine pour voir le formulaire.
* Coller une URL ICS complète (si tu veux la mettre dans Google Calendar, encode l'URL) :

```
https://ics-cleaner.onrender.com/clean_ics?url=<URL_ENCODEE>
```

---

## Mettre le lien dans Google Calendar (abonnement)

1. Copier l'URL publique fournie par Render et y ajouter le paramètre `url` encodé.
2. Dans Google Calendar → `+` à côté de "Autres agendas" → "Depuis URL" → coller l'URL.
3. Google va interroger periodiquement cette URL et afficher le calendrier nettoyé.

> Remarque : la fréquence de rafraîchissement dépend de Google (souvent toutes les 12–24h).

---

## Options avancées et améliorations possibles

* **Cache côté service** : pour réduire les appels au serveur source, tu peux ajouter un cache (ex : TTL 1h en mémoire ou Redis).
* **Authentification des URLs** : si l'ICS nécessite un token, tu peux autoriser l'utilisateur à saisir un header (Bearer) ou stocker des credentials de façon sécurisée.
* **Support complet iCalendar** : gérer TZID, RRULE, EXDATE, RECURRENCE-ID pour les événements récurrents (biblios plus avancées ou logique sur mesure).
* **Serveurless / Cloudflare Workers** : pour disponibilité instantanée et faible latence, selon le modèle de coût.

---

## Sécurité & confidentialité

* **verify=False** : utilisé pour compatibilité avec certains serveurs. En production, si possible, active `verify=True` et fournisse un certificat valide. `verify=False` désactive la vérification SSL et peut exposer à des attaques Man-in-the-Middle.
* **Ne pas rendre publique** une URL contenant des tokens ou des identifiants. Si tu dois gérer des agendas privés, implémente OAuth2 ou stockage sécurisé des tokens.
* **Logs** : évite d’enregistrer des contenus d’événements sensibles dans des logs publics.

---

## Dépannage courant

* **Erreur 500 lors du téléchargement** :

  * Assure-toi d'encoder l'URL complète (les `&` posent problème dans une query GET). Utilise le formulaire POST pour éviter l'encodage manuel.
  * Certains serveurs refusent les agents `python-requests` → User-Agent navigateur ajouté.
  * Si certificat invalide, `verify=False` permet de contourner, mais attention sécurité.

* **Google Calendar n’affiche pas les changements** : attendre 12–24h (rafraîchissement coté Google).

* **Le flux contient encore des titres non nettoyés** : adapter la regex dans `app.py` et tester localement.

---

## Personnalisation rapide (exemples)

* Supprimer plusieurs mots-clés au début (ex : `N5* - ` ou `TP* - `) :

```python
clean_name = re.sub(r"^\s*(?:N5\S*|TP\S*)\s*-\s*", "", ev.name)
```

* Supprimer les événements dont le titre correspond à une liste :

```python
BLACKLIST = ["sport du jeudi activités différées", "examen reporté"]
if ev.name and any(k in ev.name.lower() for k in BLACKLIST):
    continue
```

---

