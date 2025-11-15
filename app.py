from flask import render_template, request, jsonify
import requests
import config
from models import Trail, RouteType, Difficulty, TrailTag, Location, User

app = config.connex_app
app.add_api(config.basedir / "swagger.yml")

# ---------- Flask routes ----------

@app.route("/")
def home():
    trails = Trail.query.all()
    return render_template("home.html", trails=trails)

# ---------- Login route ----------

@app.route("/login", methods=["POST"])
def login():
    data = request.json  # gets JSON from front-end
    # Forward the POST to the Auth API
    resp = requests.post(
        "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users",
        json=data
    )
    try:
        # Return JSON to front-end
        return jsonify(resp.json()), resp.status_code
    except ValueError:
        # If response is not JSON, return raw text
        return resp.text, resp.status_code

# ---------- Run app ----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
