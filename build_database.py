from datetime import datetime
from config import app, db
from sqlalchemy import text
from models import (
    Trail, Waypoint, RouteType, Difficulty, TrailTag,
    Location, User, Activity, Photo, UserList
)

with app.app_context():

    create_schema_sql = """
    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'CW2')
    BEGIN
        EXEC('CREATE SCHEMA CW2');
    END
    """
    db.session.execute(text(create_schema_sql))
    db.session.commit()


    db.session.execute(
        text("DROP VIEW IF EXISTS CW2.v_trail_full_details")
        .execution_options(autocommit=True)
    )

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

    tables_to_create = [
        table 
        for table in db.metadata.sorted_tables
        if not table.info.get("is_view")
    ]

    db.metadata.create_all(db.engine, tables=tables_to_create)

    db.session.commit()

    print("Tables dropped and recreated successfully.")


    # Locations
    location_objs = []
    for name in ["Forest Park", "River Valley"]:
        loc = Location(
            location_name=name,
            created_at=datetime.now(),
            updated_at=None
        )
        db.session.add(loc)
        location_objs.append(loc)
    db.session.commit()

    # Users
    users_data = [
        {"username": "Grace", "email": "grace@plymouth.ac.uk", "role": "admin"},
        {"username": "Tim Berners-Lee", "email": "tim@plymouth.ac.uk", "role": "admin"},
        {"username": "Ada Lovelace", "email": "ada@plymouth.ac.uk", "role": "user"}
    ]
    user_objs = []
    for u in users_data:
        user = User(
            **u,
            created_at=datetime.now(),
            updated_at=None
        )
        db.session.add(user)
        user_objs.append(user)
    db.session.commit()

    # Route Types
    route_type_objs = []
    for name in ["Loop", "Out & Back", "Point to Point"]:
        rt = RouteType(
            route_type_name=name,
            created_at=datetime.now(),
            updated_at=None
        )
        db.session.add(rt)
        route_type_objs.append(rt)
    db.session.commit()

    # Difficulties
    difficulty_objs = []
    for name in ["Easy", "Moderate", "Hard"]:
        d = Difficulty(
            difficulty_name=name,
            created_at=datetime.now(),
            updated_at=None
        )
        db.session.add(d)
        difficulty_objs.append(d)
    db.session.commit()

    # Trail Tags
    tag_objs = {}
    for name in ["Forest", "Scenic", "River", "Mountain", "Historic"]:
        t = TrailTag(
            trail_tag_name=name,
            created_at=datetime.now(),
            updated_at=None
        )
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

        new_trail = Trail(
            **t,
            created_at=datetime.now(),
            updated_at=None
        )
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
            user_id=user_objs[2].user_id,
            length=5.2,
            elevation_gain=120.5,
            moving_time=6000,
            total_time=7500,
            calories=500,
            avg_pace=12.3,
            notes="Morning hike through the forest",
            rating=5,
            visibility="public",
            created_at=datetime.now(),
            updated_at=None
        ),
        Activity(
            trail_id=trail_objs[1].trail_id,
            user_id=user_objs[0].user_id,
            length=3.8,
            elevation_gain=50,
            moving_time=4500,
            total_time=6000,
            calories=350,
            avg_pace=11.0,
            notes="Evening walk along the river",
            rating=4,
            visibility="public",
            created_at=datetime.now(),
            updated_at=None
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
            photo_url="https://www.alltrails.com/api/alltrails/v2/trails/10483180/photos/0?size=larger_wide&key=3p0t5s6b5g4g0e8k3c1j3w7y5c3m4t8i",
            caption="Beautiful forest view",
            created_at=datetime.now(),
            updated_at=None
        ),
        Photo(
            user_id=user_objs[1].user_id,
            activity_id=None,
            trail_id=trail_objs[0].trail_id, 
            photo_url="https://www.alltrails.com/api/alltrails/v2/trails/10030115/photos/0?size=larger_wide&key=3p0t5s6b5g4g0e8k3c1j3w7y5c3m4t8i",
            caption="Walking along the trail",
            created_at=datetime.now(),
            updated_at=None
        ),
        Photo(
            user_id=user_objs[2].user_id,
            activity_id=sample_activities[1].activity_id, 
            trail_id=trail_objs[1].trail_id, 
            photo_url="https://images.squarespace-cdn.com/content/v1/646648772e4407356e7ff993/b93bb174-3528-4fca-99ba-0688d6a43651/Mam+Tor+sunset",
            caption="Sunset from the mountain peak",
            created_at=datetime.now(),
            updated_at=None
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
            trail_id=trail_objs[0].trail_id,
            visibility="public",
            created_at=datetime.now(),
            updated_at=None
        ),
        UserList(
            name="Weekend Plans",
            user_id=user_objs[1].user_id,\
            trail_id=trail_objs[1].trail_id,
            visibility="public",
            created_at=datetime.now(),
            updated_at=None
        )
    ]

    for ul in sample_lists:
        db.session.add(ul)
    db.session.commit()

    print("Database fully built with sample data")


    create_view_sql = """
    CREATE VIEW CW2.v_trail_full_details AS
    SELECT
        t.trail_id,
        t.trail_name,
        t.description,
        t.length,
        rt.route_type_name AS route_type,
        d.difficulty_name AS difficulty,
        l.location_name AS location,
        u.username AS created_by,
        (
            SELECT STRING_AGG(ul.name, ', ')
            FROM CW2.user_lists ul
            WHERE ul.trail_id = t.trail_id
        ) AS user_lists,
        (
            SELECT STRING_AGG(ttg.trail_tag_name, ', ')
            FROM CW2.trail_trailtags ttt
            JOIN CW2.trail_tags ttg ON ttt.trail_tag_id = ttg.trail_tag_id
            WHERE ttt.trail_id = t.trail_id
        ) AS tags,
        COUNT(DISTINCT a.activity_id) AS total_activities,
        AVG(CAST(a.rating AS FLOAT)) AS avg_rating,
        COUNT(DISTINCT p.photo_id) AS total_photos,
        COUNT(DISTINCT w.waypoint_id) AS total_waypoints
    FROM CW2.trails t
    JOIN CW2.route_types rt ON t.route_type_id = rt.route_type_id
    JOIN CW2.difficulties d ON t.difficulty_id = d.difficulty_id
    JOIN CW2.locations l ON t.location_id = l.location_id
    JOIN CW2.users u ON t.created_by = u.user_id
    LEFT JOIN CW2.activities a ON t.trail_id = a.trail_id
    LEFT JOIN CW2.photos p ON t.trail_id = p.trail_id
    LEFT JOIN CW2.waypoints w ON t.trail_id = w.trail_id
    GROUP BY
        t.trail_id,
        t.trail_name,
        t.description,
        t.length,
        rt.route_type_name,
        d.difficulty_name,
        l.location_name,
        u.username;
    """
    escaped_sql = create_view_sql.replace("'", "''")

    db.session.execute(
        text(f"EXEC('{escaped_sql}')")
    )
    db.session.commit()
