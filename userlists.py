from flask import jsonify, abort
from config import db
from models import UserList, UserListSchema, User, Trail
from sqlalchemy.exc import IntegrityError

userlist_schema = UserListSchema()
userlists_schema = UserListSchema(many=True)


# VALIDATION HELPERS
def validate_user(user_id):
    user = User.query.get(user_id)
    if not user:
        abort(404, f"User {user_id} not found.")
    return user


def validate_trail(trail_id):
    trail = Trail.query.get(trail_id)
    if not trail:
        abort(404, f"Trail {trail_id} not found.")
    return trail


def validate_user_by_name(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        abort(404, f"User '{username}' not found.")
    return user


def validate_trail_by_name(trail_name):
    trail = Trail.query.filter_by(trail_name=trail_name).first()
    if not trail:
        abort(404, f"Trail '{trail_name}' not found.")
    return trail


def read_all():
    userlists = UserList.query.all()

    results = []
    for ul in userlists:
        ul_dict = userlist_schema.dump(ul)

        # Convert IDs to names for output
        ul_dict["username"] = ul.user.username if ul.user else None

        if ul.trail_id:
            trail = Trail.query.get(ul.trail_id)
            ul_dict["trail_name"] = trail.trail_name if trail else None
        else:
            ul_dict["trail_name"] = None

        ul_dict.pop("user_id", None)
        ul_dict.pop("trail_id", None)
        ul_dict.pop("user_list_id", None)

        results.append(ul_dict)

    return jsonify(results), 200


def read_one(user_list_id):
    ul = UserList.query.get(user_list_id)
    if not ul:
        abort(404, f"UserList {user_list_id} not found.")

    ul_dict = userlist_schema.dump(ul)

    ul_dict["username"] = ul.user.username if ul.user else None

    if ul.trail_id:
        trail = Trail.query.get(ul.trail_id)
        ul_dict["trail_name"] = trail.trail_name if trail else None
    else:
        ul_dict["trail_name"] = None

    ul_dict.pop("user_id", None)
    ul_dict.pop("trail_id", None)
    ul_dict.pop("user_list_id", None)

    return jsonify(ul_dict), 200


def create(user_list_data):
    try:
        username = user_list_data.get("user_name")
        trail_name = user_list_data.get("trail_name")
        list_name = user_list_data.get("name")

        if not username:
            abort(400, "Missing required field: user_name")
        if not list_name:
            abort(400, "Missing required field: name")

        # Validate Visibility
        allowed_visibility = ["public", "private", "friends"]
        visibility = user_list_data.get("visibility")

        if visibility:
            if visibility.lower() not in allowed_visibility:
                abort(400, description=f"Invalid visibility '{visibility}'. Allowed: Public, Private, Friends.")
            user_list_data["visibility"] = visibility.lower() 
        else:
            user_list_data["visibility"] = "public"

        # Duplicate name check
        existing = UserList.query.filter(
            UserList.name.ilike(list_name)
        ).first()

        if existing:
            abort(400, description=f"User list name '{list_name}' already exists.")

        user = validate_user_by_name(username)

        if trail_name:
            trail = validate_trail_by_name(trail_name)
            user_list_data["trail_id"] = trail.trail_id
        else:
            user_list_data["trail_id"] = None

        user_list_data["user_id"] = user.user_id

        user_list_data.pop("user_name", None)
        user_list_data.pop("trail_name", None)

        new_list = userlist_schema.load(user_list_data, session=db.session)
        db.session.add(new_list)
        db.session.commit()

        ul_dict = userlist_schema.dump(new_list)
        ul_dict["user_name"] = user.username
        ul_dict["trail_name"] = trail_name

        ul_dict.pop("user_id", None)
        ul_dict.pop("trail_id", None)
        ul_dict.pop("user_list_id", None)

        return jsonify(ul_dict), 201

    except IntegrityError as e:
        db.session.rollback()
        error_text = str(e.orig).lower()
        if "unique" in error_text or "duplicate" in error_text:
            abort(400, description="A list with this name already exists. Please choose a different name.")

        abort(400, description="Database constraint error.")

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


def update(user_list_id, user_list_data):
    try:
        ul = UserList.query.get(user_list_id)
        if not ul:
            abort(404, f"UserList {user_list_id} not found.")

        # Validate visibility (only if sent)
        allowed_visibility = ["public", "private", "friends"]
        visibility = user_list_data.get("visibility")

        if visibility is not None:  # user wants to update it
            if visibility.lower() not in allowed_visibility:
                abort(400, description=f"Invalid visibility '{visibility}'. Allowed: Public, Private, Friends.")
            ul.visibility = visibility.lower() 

        if "user_name" in user_list_data:
            username = user_list_data.pop("user_name")
            user = validate_user_by_name(username)
            ul.user_id = user.user_id

        if "trail_name" in user_list_data:
            trail_name = user_list_data.pop("trail_name")
            if trail_name:
                trail = validate_trail_by_name(trail_name)
                ul.trail_id = trail.trail_id
            else:
                ul.trail_id = None

        for key, value in user_list_data.items():
            setattr(ul, key, value)

        db.session.commit()

        ul_dict = userlist_schema.dump(ul)
        ul_dict["user_name"] = ul.user.username if ul.user else None

        if ul.trail_id:
            trail = Trail.query.get(ul.trail_id)
            ul_dict["trail_name"] = trail.trail_name if trail else None
        else:
            ul_dict["trail_name"] = None

        ul_dict.pop("user_id", None)
        ul_dict.pop("trail_id", None)
        ul_dict.pop("user_list_id", None)

        return jsonify(ul_dict), 200

    except IntegrityError as e:
        db.session.rollback()
        error_text = str(e.orig).lower()
        if "unique" in error_text or "duplicate" in error_text:
            abort(400, description="A list with this name already exists. Please choose a different name.")

        abort(400, description="Database constraint error.")

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


def delete(user_list_id):
    ul = UserList.query.get(user_list_id)
    if not ul:
        abort(404, f"UserList {user_list_id} not found.")

    db.session.delete(ul)
    db.session.commit()

    return {"message": f"UserList {user_list_id} deleted"}, 200
