from flask import render_template, request, jsonify
import requests
import config
from models import Trail, Activity, UserList

app = config.connex_app
app.add_api(config.basedir / "swagger.yml")

@app.route("/")
def home():
    trails = Trail.query.all()
    activities = Activity.query.all()
    activities_with_trail = []
    for act in activities:
        trail_name = None
        if act.trail_id:
            trail = Trail.query.get(act.trail_id)
            trail_name = trail.trail_name if trail else None
        act.trail_name = trail_name
        activities_with_trail.append(act)
    userlists = UserList.query.all()
    return render_template("home.html", trails=trails, activities=activities_with_trail, userlists=userlists)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8001, debug=True)
