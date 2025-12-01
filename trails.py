from flask import abort, jsonify
from config import db
from models import (
    Trail, Waypoint, TrailTag, Activity, Photo,
    User, Location, RouteType, Difficulty, UserList,
    TrailFullDetails,  
    trail_schema, trail_full_schema,
)
import requests
from sqlalchemy.exc import IntegrityError

# VALIDATION HELPERS
def validate_user(user_id):
    """Validate user locally or via Auth API."""
    user = User.query.get(user_id)
    if not user:
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


def validate_fk(model, id_, name):
    """Generic FK validation."""
    obj = model.query.get(id_)
    if not obj:
        abort(404, f"{name} {id_} not found")
    return obj


# READ ALL TRAILS
def read_all():
    trails = TrailFullDetails.query.all()

    results = []
    for trail in trails:
        # Waypoints
        waypoints = Waypoint.query.filter_by(trail_id=trail.trail_id).order_by(Waypoint.sequence_no).all()
        waypoints_list = [
            {
                "waypoint_name": wp.waypoint_name,
                "description": wp.description,
                "latitude": float(wp.latitude),
                "longitude": float(wp.longitude),
                "sequence_no": wp.sequence_no,
            } for wp in waypoints
        ]

        # Only public activities
        activities = Activity.query.filter_by(trail_id=trail.trail_id, visibility="public").all()
        activities_list = []
        for act in activities:
            photos = Photo.query.filter_by(activity_id=act.activity_id).all()
            photos_list = [
                {
                    "photo_url": p.photo_url,
                    "caption": p.caption,
                    "created_at": p.created_at.isoformat(),
                } for p in photos
            ]

            activities_list.append({
                "user_name": User.query.get(act.user_id).username if User.query.get(act.user_id) else None,
                "length": float(act.length) if act.length else None,
                "elevation_gain": float(act.elevation_gain) if act.elevation_gain else None,
                "moving_time": act.moving_time,
                "total_time": act.total_time,
                "calories": act.calories,
                "avg_pace": float(act.avg_pace) if act.avg_pace else None,
                "notes": act.notes,
                "rating": act.rating,
                "photos": photos_list
            })

        # User lists for this trail
        user_lists_objs = UserList.query.filter_by(trail_id=trail.trail_id).all()
        user_lists = [
            {
                "user_name": User.query.get(ul.user_id).username if User.query.get(ul.user_id) else None,
                "name": ul.name,
                "visibility": ul.visibility
            } for ul in user_lists_objs
        ]

        trail_dict = trail_full_schema.dump(trail)
        trail_dict.pop("total_waypoints", None)
        trail_dict.pop("total_activities", None)
        trail_dict.pop("total_photos", None)
        trail_dict.pop("trail_id", None)

        trail_dict["waypoints"] = waypoints_list
        trail_dict["activities"] = activities_list
        trail_dict["user_lists"] = user_lists

        results.append(trail_dict)

    return jsonify(results), 200


# READ ONE TRAIL
def read_one(trail_id):
    trail = TrailFullDetails.query.get(trail_id)
    if not trail:
        abort(404, f"Trail {trail_id} not found")

    waypoints = Waypoint.query.filter_by(trail_id=trail.trail_id).order_by(Waypoint.sequence_no).all()

    activities = Activity.query.filter_by(trail_id=trail.trail_id, visibility="public").all()
    activities_list = []
    for act in activities:
        photos = Photo.query.filter_by(activity_id=act.activity_id).all()
        photos_list = [
            {
                "photo_url": p.photo_url,
                "caption": p.caption,
                "created_at": p.created_at.isoformat(),
            } for p in photos
        ]

        activities_list.append({
            "user_name": User.query.get(act.user_id).username if User.query.get(act.user_id) else None,
            "length": float(act.length) if act.length else None,
            "elevation_gain": float(act.elevation_gain) if act.elevation_gain else None,
            "moving_time": act.moving_time,
            "total_time": act.total_time,
            "calories": act.calories,
            "avg_pace": float(act.avg_pace) if act.avg_pace else None,
            "notes": act.notes,
            "rating": act.rating,
            "photos": photos_list
        })

    user_lists = UserList.query.filter_by(trail_id=trail.trail_id).all()
    user_lists_list = [
        {
            "name": ul.name, 
            "user_name": User.query.get(ul.user_id).username if User.query.get(ul.user_id) else None,
            "visibility": ul.visibility
         } for ul in user_lists
    ]

    trail_dict = trail_full_schema.dump(trail)
    trail_dict.pop("total_waypoints", None)
    trail_dict["waypoints"] = [
        {
            "waypoint_name": wp.waypoint_name,
            "description": wp.description,
            "latitude": float(wp.latitude),
            "longitude": float(wp.longitude),
            "sequence_no": wp.sequence_no,
        } for wp in waypoints
    ]
    trail_dict["activities"] = activities_list
    trail_dict["user_lists"] = user_lists_list

    return jsonify(trail_dict), 200



# CREATE TRAIL
def create(trail_data):
    try:
        # Extract name-based fields
        created_by_name = trail_data.pop("created_by")
        route_type_name = trail_data.pop("route_type_name", None)
        difficulty_name = trail_data.pop("difficulty_name", None)
        location_name = trail_data.pop("location_name", None)

        # Convert user name → user_id (case-insensitive)
        user = User.query.filter(User.username.ilike(created_by_name)).first()
        if not user:
            abort(400, description=f"User '{created_by_name}' not found")
        trail_data["created_by"] = user.user_id

        allowed_route_types = ["loop", "out & back", "point to point"]
        if route_type_name:
            if route_type_name.lower() not in allowed_route_types:
                abort(400, description=f"Invalid route type '{route_type_name}'. Allowed values: Loop, Out & Back, Point to Point.")

            rt = RouteType.query.filter(RouteType.route_type_name.ilike(route_type_name)).first()
            if not rt:
                abort(400, description=f"Route type '{route_type_name}' does not exist in the database. Please insert it first.")
            trail_data["route_type_id"] = rt.route_type_id


        allowed_difficulties = ["easy", "moderate", "hard"]
        if difficulty_name:
            if difficulty_name.lower() not in allowed_difficulties:
                abort(400, description=f"Invalid difficulty '{difficulty_name}'. Allowed values: Easy, Moderate, Hard.")

            df = Difficulty.query.filter(Difficulty.difficulty_name.ilike(difficulty_name)).first()
            if not df:
                abort(400, description=f"Difficulty '{difficulty_name}' does not exist in the database. Please insert it first.")
            trail_data["difficulty_id"] = df.difficulty_id


        if location_name:
            loc = Location.query.filter(Location.location_name.ilike(location_name)).first()
            if not loc:
                loc = Location(location_name=location_name)
                db.session.add(loc)
                db.session.flush()
            trail_data["location_id"] = loc.location_id

        # Process nested items
        waypoints_data = trail_data.pop("waypoints", [])
        tags_data = trail_data.pop("tags", [])
        photos_data = trail_data.pop("photos", [])

        # Create trail
        new_trail = trail_schema.load(trail_data, session=db.session)
        db.session.add(new_trail)
        db.session.flush()  # Ensure trail_id is available for nested items

        # Waypoints
        for wp in waypoints_data:
            new_trail.waypoints.append(Waypoint(**wp))

        # Tags (create if missing)
        for t in tags_data:
            tag_name = t.get("trail_tag_name")
            if not tag_name:
                continue
            tag = TrailTag.query.filter(TrailTag.trail_tag_name.ilike(tag_name)).first()
            if not tag:
                tag = TrailTag(trail_tag_name=tag_name)
                db.session.add(tag)
                db.session.flush()
            new_trail.tags.append(tag)

        # Photos
        for p in photos_data:
            p["user_id"] = user.user_id              # photo owner = creator of trail
            p["trail_id"] = new_trail.trail_id       # link photo to the trail

            new_trail.photos.append(Photo(**p))

        # Commit everything
        db.session.commit()
        result = trail_schema.dump(new_trail)
        if new_trail.route_type:
            result["route_type"] = new_trail.route_type.route_type_name
        if new_trail.difficulty:
            result["difficulty"] = new_trail.difficulty.difficulty_name
        if new_trail.location:
            result["location"] = new_trail.location.location_name
        result.pop("difficulty_id", None)
        result.pop("location_id", None)
        result.pop("route_type_id", None)
        result.pop("trail_id", None)
        result.pop("creator", None)
        result.pop("activities", None)
        result.pop("user_lists", None)
        result.pop("updated_by", None)

        # Remove trail_id from waypoints
        for wp in result.get("waypoints", []):
            wp.pop("trail_id", None)
            wp.pop("waypoint_id", None)
            wp.pop("created_at", None)

        for tag in result.get("tags", []):
            tag.pop("trail_tag_id", None)
            tag.pop("created_at", None)
            tag.pop("updated_at", None)

        result["created_by"] = new_trail.creator.username if new_trail.creator else None

        return result, 201
    
    except IntegrityError as e:
        db.session.rollback()

        # Check if UNIQUE constraint failed (duplicate trail_name)
        if "UQ__trails" in str(e.orig) or "duplicate key" in str(e.orig):
            abort(400, description="Trail name already exists. Please choose a different name.")

        # Other DB integrity errors
        abort(400, description="Database constraint error.")

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


# UPDATE TRAIL
def update(trail_id, trail_data):
    try:
        # Get existing trail
        trail = Trail.query.get(trail_id)
        if not trail:
            abort(404, description=f"Trail with id {trail_id} not found")

        updated_by_name = trail_data.pop("updated_by", None)
        route_type_name = trail_data.pop("route_type_name", None)
        difficulty_name = trail_data.pop("difficulty_name", None)
        location_name = trail_data.pop("location_name", None)

        if updated_by_name:
            user = User.query.filter(User.username.ilike(updated_by_name)).first()
            if not user:
                abort(400, description=f"User '{updated_by_name}' not found")
            trail_data["updated_by"] = user.user_id

        allowed_route_types = ["loop", "out & back", "point to point"]
        if route_type_name:
            if route_type_name.lower() not in allowed_route_types:
                abort(400, description=f"Invalid route type '{route_type_name}'. Allowed values: Loop, Out & Back, Point to Point.")

            rt = RouteType.query.filter(RouteType.route_type_name.ilike(route_type_name)).first()
            if not rt:
                abort(400, description=f"Route type '{route_type_name}' does not exist in the database. Please insert it first.")
            trail_data["route_type_id"] = rt.route_type_id


        allowed_difficulties = ["easy", "moderate", "hard"]
        if difficulty_name:
            if difficulty_name.lower() not in allowed_difficulties:
                abort(400, description=f"Invalid difficulty '{difficulty_name}'. Allowed values: Easy, Moderate, Hard.")

            df = Difficulty.query.filter(Difficulty.difficulty_name.ilike(difficulty_name)).first()
            if not df:
                abort(400, description=f"Difficulty '{difficulty_name}' does not exist in the database. Please insert it first.")
            trail_data["difficulty_id"] = df.difficulty_id

        if location_name:
            loc = Location.query.filter(Location.location_name.ilike(location_name)).first()
            if not loc:
                loc = Location(location_name=location_name)
                db.session.add(loc)
                db.session.flush()
            trail_data["location_id"] = loc.location_id

        waypoints_data = trail_data.pop("waypoints", None)
        tags_data = trail_data.pop("tags", None)
        photos_data = trail_data.pop("photos", None)

        # Update simple fields
        for key, value in trail_data.items():
            setattr(trail, key, value)

        # Update waypoints: replace existing with new ones
        if waypoints_data is not None:
            trail.waypoints.clear()
            for wp in waypoints_data:
                trail.waypoints.append(Waypoint(**wp))

        # Update tags: replace existing with new ones (create if missing)
        if tags_data is not None:
            trail.tags.clear()
            for t in tags_data:
                tag_name = t.get("trail_tag_name")
                if not tag_name:
                    continue
                tag = TrailTag.query.filter(TrailTag.trail_tag_name.ilike(tag_name)).first()
                if not tag:
                    tag = TrailTag(trail_tag_name=tag_name)
                    db.session.add(tag)
                    db.session.flush()
                trail.tags.append(tag)

        # Update photos: replace existing with new ones
        if photos_data is not None:
            trail.photos.clear()
            for p in photos_data:
                p["user_id"] = trail.updated_by or trail.created_by
                p["trail_id"] = trail.trail_id

                trail.photos.append(Photo(**p))

        db.session.commit()
        db.session.commit()
        result = trail_schema.dump(trail)
        if trail.route_type:
            result["route_type"] = trail.route_type.route_type_name
        if trail.difficulty:
            result["difficulty"] = trail.difficulty.difficulty_name
        if trail.location:
            result["location"] = trail.location.location_name
        result.pop("difficulty_id", None)
        result.pop("location_id", None)
        result.pop("route_type_id", None)
        result.pop("trail_id", None)
        result.pop("creator", None)
        result.pop("activities", None)
        result.pop("user_lists", None)
        result.pop("updated_by", None)

        # Remove trail_id from waypoints
        for wp in result.get("waypoints", []):
            wp.pop("trail_id", None)
            wp.pop("waypoint_id", None)
            wp.pop("created_at", None)

        for tag in result.get("tags", []):
            tag.pop("trail_tag_id", None)
            tag.pop("created_at", None)
            tag.pop("updated_at", None)

        result["created_by"] = trail.creator.username if trail.creator else None

        return result, 200

    except IntegrityError as e:
        db.session.rollback()

        # Check if UNIQUE constraint failed (duplicate trail_name)
        if "UQ__trails" in str(e.orig) or "duplicate key" in str(e.orig):
            abort(400, description="Trail name already exists. Please choose a different name.")

        # Other DB integrity errors
        abort(400, description="Database constraint error.")

    except Exception as e:
        db.session.rollback()
        abort(500, description=str(e))


# DELETE TRAIL
def delete(trail_id):
    trail = Trail.query.get(trail_id)
    if not trail:
        abort(404, f"Trail {trail_id} not found")

    db.session.delete(trail)
    db.session.commit()
    return {"message": f"Trail {trail_id} deleted"}, 200

