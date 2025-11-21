from flask import Flask, request, Response, render_template_string
from ics import Calendar, Event
import requests
import re
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# --- Interface HTML simple ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>Nettoyeur d'agenda ICS</title>
  <style>
    body { font-family: sans-serif; max-width: 600px; margin: 40px auto; }
    input[type=text] { width: 100%; padding: 10px; font-size: 1rem; }
    button { padding: 10px 15px; margin-top: 10px; font-size: 1rem; cursor: pointer; }
    .msg { margin-top: 20px; color: #555; }
  </style>
</head>
<body>
  <h2>🧹 Nettoyeur d'agenda ICS</h2>
  <p>Collez l’URL de votre calendrier ICS ci-dessous (par ex. INP Toulouse) :</p>
  <form method="POST" action="/clean_ics">
    <input type="text" name="url" placeholder="https://..." required>
    <button type="submit">Nettoyer et télécharger</button>
  </form>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_PAGE)


@app.route("/clean_ics", methods=["GET", "POST"])
def clean_ics():
    if request.method == "POST":
        url = request.form.get("url")
    else:
        url = request.args.get("url")

    if not url:
        return "Paramètre 'url' manquant", 400

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept": "text/calendar, text/plain, */*",
    }

    try:
        r = requests.get(url, headers=headers, timeout=20, verify=False)
        r.raise_for_status()
        content = r.content.decode(errors="ignore")
    except Exception as e:
        return f"❌ Erreur lors du téléchargement : {e}", 500

    try:
        cal = Calendar(content)
    except Exception as e:
        return f"❌ Erreur lors du parsing ICS : {e}", 500

    new_cal = Calendar()
    
    for ev in cal.events:
    # 🛑 Filtrer les événements à supprimer

      BLACKLIST = ["sport du jeudi activités différées"]
      if ev.name and any(k in ev.name.lower() for k in BLACKLIST):
          continue  # on saute cet événement
  
      new_ev = Event()
      new_ev.begin = ev.begin
      new_ev.end = ev.end
      new_ev.location = ev.location
      new_ev.description = ev.description
  
      if ev.name:
          # Supprime le mot commençant par N5,6,7 et le tiret suivant
          clean_name = re.sub(r"^\s*(?:N5\S*|N6\S*|N7\S*|N8\S*|N9\S*|N10\S*)\s*-\s*", "", ev.name)
          clean_name = re.sub(r"^\s*N5\S*\s*-\s*", "", ev.name)
          new_ev.name = clean_name.strip()
  
      new_cal.events.add(new_ev)


    response = Response(str(new_cal), mimetype="text/calendar")
    response.headers["Content-Disposition"] = "attachment; filename=clean.ics"
    return response


if __name__ == "__main__":
    app.run(port=5000, debug=True)




