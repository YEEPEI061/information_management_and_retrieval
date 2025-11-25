from flask import jsonify, abort
from config import db
from models import UserList, UserListSchema, User, Trail

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

    return jsonify(ul_dict), 200


def create(userlist_data):
    try:
        username = userlist_data.get("user_name")
        trail_name = userlist_data.get("trail_name")

        if not username:
            abort(400, "Missing required field: user_name")

        user = validate_user_by_name(username)

        if trail_name:
            trail = validate_trail_by_name(trail_name)
            userlist_data["trail_id"] = trail.trail_id
        else:
            userlist_data["trail_id"] = None

        userlist_data["user_id"] = user.user_id

        userlist_data.pop("user_name", None)
        userlist_data.pop("trail_name", None)

        new_list = userlist_schema.load(userlist_data, session=db.session)
        db.session.add(new_list)
        db.session.commit()

        ul_dict = userlist_schema.dump(new_list)
        ul_dict["user_name"] = user.username
        ul_dict["trail_name"] = trail_name

        ul_dict.pop("user_id", None)
        ul_dict.pop("trail_id", None)

        return jsonify(ul_dict), 201

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


def update(user_list_id, userlist_data):
    try:
        ul = UserList.query.get(user_list_id)
        if not ul:
            abort(404, f"UserList {user_list_id} not found.")

        if "username" in userlist_data:
            username = userlist_data.pop("user_name")
            user = validate_user_by_name(username)
            ul.user_id = user.user_id

        if "trail_name" in userlist_data:
            trail_name = userlist_data.pop("trail_name")
            if trail_name:
                trail = validate_trail_by_name(trail_name)
                ul.trail_id = trail.trail_id
            else:
                ul.trail_id = None

        for key, value in userlist_data.items():
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

        return jsonify(ul_dict), 200

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
