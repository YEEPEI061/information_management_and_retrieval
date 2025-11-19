from config import app, db
from sqlalchemy import text
from models import (
    Trail, Waypoint, RouteType, Difficulty, TrailTag,
    Location, User, Activity, Photo, UserList
)

with app.app_context():

    drop_fks_sql = """
    DECLARE @sql NVARCHAR(MAX) = '';

    SELECT @sql += 'ALTER TABLE [' + s.name + '].[' + t.name + '] DROP CONSTRAINT [' + fk.name + '];'
    FROM sys.foreign_keys AS fk
    INNER JOIN sys.tables AS t ON fk.parent_object_id = t.object_id
    INNER JOIN sys.schemas AS s ON t.schema_id = s.schema_id
    WHERE s.name = 'CW2';

    EXEC sp_executesql @sql;
    """
    db.session.execute(text(drop_fks_sql))
    db.session.commit()

    # DROP TABLES (ORDERED)
    tables = [
        "photos",
        "activities",
        "waypoints",
        "user_lists",
        "trail_trailtags",
        "trails",
        "trail_tags",
        "locations",
        "route_types",
        "difficulties",
        "users"
    ]

    for table in tables:
        db.session.execute(text(f"DROP TABLE IF EXISTS CW2.{table}"))

    db.session.commit()

    db.create_all()
    db.session.commit()

    print("Tables dropped and recreated successfully.")


    # Locations
    location_objs = []
    for name in ["Forest Park", "River Valley"]:
        loc = Location(location_name=name)
        db.session.add(loc)
        location_objs.append(loc)
    db.session.commit()

    # Users
    users_data = [
        {"username": "Grace", "email": "grace@plymouth.ac.uk", "role": "user"},
        {"username": "Tim Berners-Lee", "email": "tim@plymouth.ac.uk", "role": "user"},
        {"username": "Ada Lovelace", "email": "ada@plymouth.ac.uk", "role": "user"}
    ]
    user_objs = []
    for u in users_data:
        user = User(**u)
        db.session.add(user)
        user_objs.append(user)
    db.session.commit()

    # Route Types
    route_type_objs = []
    for name in ["Loop", "Out & Back", "Point to Point"]:
        rt = RouteType(route_type_name=name)
        db.session.add(rt)
        route_type_objs.append(rt)
    db.session.commit()

    # Difficulties
    difficulty_objs = []
    for name in ["Easy", "Moderate", "Hard"]:
        d = Difficulty(difficulty_name=name)
        db.session.add(d)
        difficulty_objs.append(d)
    db.session.commit()

    # Trail Tags
    tag_objs = {}
    for name in ["Forest", "Scenic", "River", "Mountain", "Historic"]:
        t = TrailTag(trail_tag_name=name)
        db.session.add(t)
        tag_objs[name] = t
    db.session.commit()

    # TRAILS (WAYPOINTS + TAGS)
    sample_trails = [
        {
            "trail_name": "Forest Adventure",
            "description": "A scenic forest trail.",
            "length": 5.2,
            "elevation_gain": 120.5,
            "estimated_time": 1.5,
            "route_type_id": route_type_objs[0].route_type_id,
            "difficulty_id": difficulty_objs[0].difficulty_id,
            "location_id": location_objs[0].location_id,
            "created_by": next(u.user_id for u in user_objs if u.email == "ada@plymouth.ac.uk"),
            "waypoints": [
                {"waypoint_name": "Start", "latitude": 3.1408, "longitude": 101.6869, "sequence_no": 1},
                {"waypoint_name": "Scenic View", "latitude": 3.1410, "longitude": 101.6871, "sequence_no": 2},
            ],
            "tags": ["Forest", "Scenic"]
        },
        {
            "trail_name": "River Walk",
            "description": "Trail along the river.",
            "length": 3.8,
            "elevation_gain": 50,
            "estimated_time": 1.0,
            "route_type_id": route_type_objs[1].route_type_id,
            "difficulty_id": difficulty_objs[1].difficulty_id,
            "location_id": location_objs[1].location_id,
            "created_by": next(u.user_id for u in user_objs if u.email == "grace@plymouth.ac.uk"),
            "waypoints": [
                {"waypoint_name": "Start", "latitude": 3.1420, "longitude": 101.6880, "sequence_no": 1},
                {"waypoint_name": "Bridge", "latitude": 3.1425, "longitude": 101.6885, "sequence_no": 2},
            ],
            "tags": ["River", "Scenic"]
        },
    ]

    trail_objs = []

    for t in sample_trails:
        tags = t.pop("tags", [])
        waypoints = t.pop("waypoints", [])

        new_trail = Trail(**t)
        db.session.add(new_trail)

        for wp in waypoints:
            new_trail.waypoints.append(Waypoint(**wp))

        for tag_name in tags:
            new_trail.tags.append(tag_objs[tag_name])

        trail_objs.append(new_trail)

    db.session.commit()

    # ACTIVITIES
    sample_activities = [
        Activity(
            trail_id=trail_objs[0].trail_id,
            user_id=user_objs[2].user_id,  # Ada
            length=5.2,
            elevation_gain=120.5,
            moving_time=60,
            total_time=75,
            calories=500,
            avg_pace=12.3,
            notes="Morning hike through the forest",
            rating=5,
            visibility="public"
        ),
        Activity(
            trail_id=trail_objs[1].trail_id,
            user_id=user_objs[0].user_id,  # Grace
            length=3.8,
            elevation_gain=50,
            moving_time=45,
            total_time=60,
            calories=350,
            avg_pace=11.0,
            notes="Evening walk along the river",
            rating=4,
            visibility="public"
        )
    ]

    for act in sample_activities:
        db.session.add(act)
    db.session.commit()

    # PHOTOS
    sample_photos = [
        Photo(
            user_id=user_objs[2].user_id,
            activity_id=sample_activities[0].activity_id, 
            trail_id=None,
            photo_url="https://example.com/forest_view.jpg",
            caption="Beautiful forest view"
        ),
        Photo(
            user_id=user_objs[1].user_id,
            activity_id=None,
            trail_id=trail_objs[0].trail_id, 
            photo_url="https://example.com/trail_path.jpg",
            caption="Walking along the trail"
        ),
        Photo(
            user_id=user_objs[2].user_id,
            activity_id=sample_activities[1].activity_id, 
            trail_id=trail_objs[1].trail_id, 
            photo_url="https://example.com/sunset_peak.jpg",
            caption="Sunset from the mountain peak"
        )
    ]

    for p in sample_photos:
        db.session.add(p)
    db.session.commit()


    # USER LISTS
    sample_lists = [
        UserList(
            name="Favorite Trails",
            user_id=user_objs[2].user_id,
            visibility="public"
        ),
        UserList(
            name="Weekend Plans",
            user_id=user_objs[1].user_id,
            visibility="public"
        )
    ]

    for ul in sample_lists:
        db.session.add(ul)
    db.session.commit()

    print("Database fully built with sample data")
