from flask import jsonify, abort
from config import db
from models import (
    Activity, ActivitySchema, Photo,
    User, Trail
)
import requests

AUTH_API_URL = "https://web.socem.plymouth.ac.uk/COMP2001/auth/api/users"

activity_schema = ActivitySchema()
activities_schema = ActivitySchema(many=True)


def validate_user(user_id):
    """Validate user locally or from external Auth API."""
    user = User.query.get(user_id)
    if not user:
        resp = requests.get(f"{AUTH_API_URL}/{user_id}")
        if resp.status_code != 200:
            abort(404, f"User {user_id} not found.")
        data = resp.json()

        user = User(
            user_id=data["user_id"],
            username=data["username"],
            email=data["email"],
            role=data["role"]
        )
        db.session.add(user)
        db.session.commit()
    return user


def validate_trail(trail_id):
    """Ensure the trail exists."""
    trail = Trail.query.get(trail_id)
    if not trail:
        abort(404, f"Trail {trail_id} not found.")
    return trail


def read_all():
    activities = Activity.query.all()

    results = []
    for act in activities:
        photos = Photo.query.filter_by(activity_id=act.activity_id).all()
        photos_list = [
            {
                "photo_id": p.photo_id,
                "photo_url": p.photo_url,
                "caption": p.caption,
                "created_at": p.created_at.isoformat(),
            }
            for p in photos
        ]

        act_dict = activity_schema.dump(act)

        act_dict["user_name"] = act.user.username if act.user else None
        trail = Trail.query.get(act.trail_id)
        act_dict["trail_name"] = trail.trail_name if trail else None


        # Remove id from output
        act_dict.pop("user_id", None)
        act_dict.pop("trail_id", None)

        act_dict["photos"] = photos_list
        results.append(act_dict)

    return jsonify(results), 200


def read_one(activity_id):
    act = Activity.query.get(activity_id)
    if not act:
        abort(404, f"Activity {activity_id} not found.")

    photos = Photo.query.filter_by(activity_id=act.activity_id).all()
    photos_list = [
        {
            "photo_id": p.photo_id,
            "photo_url": p.photo_url,
            "caption": p.caption,
            "created_at": p.created_at.isoformat(),
        }
        for p in photos
    ]

    act_dict = activity_schema.dump(act)

    act_dict["user_name"] = act.user.username if act.user else None
    trail = Trail.query.get(act.trail_id)
    act_dict["trail_name"] = trail.trail_name if trail else None


    act_dict.pop("user_id", None)
    act_dict.pop("trail_id", None)

    act_dict["photos"] = photos_list

    return jsonify(act_dict), 200



def create(activity_data):
    try:
        user_name = activity_data.get("user_name")
        trail_name = activity_data.get("trail_name")

        if not user_name or not trail_name:
            abort(400, "Missing required fields: user_name or trail_name.")

        user = User.query.filter_by(username=user_name).first()
        if not user:
            user = validate_user_by_name(user_name)
        trail = Trail.query.filter_by(trail_name=trail_name).first()
        if not trail:
            abort(404, f"Trail '{trail_name}' not found.")

        # Replace names with id for saving
        activity_data["user_id"] = user.user_id
        activity_data["trail_id"] = trail.trail_id
        activity_data.pop("user_name", None)
        activity_data.pop("trail_name", None)

        photos_data = activity_data.pop("photos", [])

        new_activity = activity_schema.load(activity_data, session=db.session)
        db.session.add(new_activity)
        db.session.flush() 

        for p in photos_data:
            p["user_id"] = user.user_id
            p["activity_id"] = new_activity.activity_id
            db.session.add(Photo(**p))

        db.session.commit()

        act_dict = activity_schema.dump(new_activity)
        act_dict["user_name"] = user.username
        act_dict["trail_name"] = trail.trail_name
        act_dict.pop("user_id", None)
        act_dict.pop("trail_id", None)
        act_dict["photos"] = [
            {
                "photo_id": p.photo_id,
                "photo_url": p.photo_url,
                "caption": p.caption,
                "created_at": p.created_at.isoformat(),
            }
            for p in Photo.query.filter_by(activity_id=new_activity.activity_id).all()
        ]

        return jsonify(act_dict), 201

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


def update(activity_id, activity_data):
    try:
        act = Activity.query.get(activity_id)
        if not act:
            abort(404, f"Activity {activity_id} not found.")

        user = act.user
        trail = Trail.query.get(act.trail_id)

        if "user_name" in activity_data:
            user_name = activity_data.pop("user_name")
            user = User.query.filter_by(username=user_name).first()
            if not user:
                user = validate_user_by_name(user_name) 
            act.user_id = user.user_id

        if "trail_name" in activity_data:
            trail_name = activity_data.pop("trail_name")
            trail = Trail.query.filter_by(trail_name=trail_name).first()
            if not trail:
                abort(404, f"Trail '{trail_name}' not found.")
            act.trail_id = trail.trail_id

        photos_data = activity_data.pop("photos", None)

        for key, value in activity_data.items():
            setattr(act, key, value)

        if photos_data is not None:
            Photo.query.filter_by(activity_id=act.activity_id).delete()
            for p in photos_data:
                p["user_id"] = act.user_id
                p["activity_id"] = act.activity_id
                db.session.add(Photo(**p))

        db.session.commit()

        act_dict = activity_schema.dump(act)
        act_dict["user_name"] = user.username if user else None
        act_dict["trail_name"] = trail.trail_name if trail else None
        act_dict.pop("user_id", None)
        act_dict.pop("trail_id", None)
        act_dict["photos"] = [
            {
                "photo_id": p.photo_id,
                "photo_url": p.photo_url,
                "caption": p.caption,
                "created_at": p.created_at.isoformat(),
            }
            for p in Photo.query.filter_by(activity_id=act.activity_id).all()
        ]

        return jsonify(act_dict), 200

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


def validate_user_by_name(username: str) -> User:
    """Validate user locally or fetch from external auth API by username."""
    user = User.query.filter_by(username=username).first()
    if user:
        return user

    # If not found locally, fetch from external Auth API
    resp = requests.get(f"{AUTH_API_URL}?username={username}")
    if resp.status_code != 200:
        abort(404, f"User '{username}' not found in Auth API.")
    data = resp.json()
    user = User(
        user_id=data["user_id"],
        username=data["username"],
        email=data.get("email"),
        role=data.get("role")
    )
    db.session.add(user)
    db.session.commit()
    return user


def delete(activity_id):
    act = Activity.query.get(activity_id)
    if not act:
        abort(404, f"Activity {activity_id} not found.")

    Photo.query.filter_by(activity_id=act.activity_id).delete()

    db.session.delete(act)
    db.session.commit()

    return {"message": f"Activity {activity_id} deleted"}, 200
