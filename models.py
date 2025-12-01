from datetime import datetime
import pytz
from config import db, ma
from marshmallow import fields, validate

class User(db.Model):
    __tablename__ = "users"
    __table_args__ = {"schema": "CW2"}
    user_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True


class Location(db.Model):
    __tablename__ = "locations"
    __table_args__ = {"schema": "CW2"}
    location_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    location_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

class LocationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Location
        load_instance = True


class RouteType(db.Model):
    __tablename__ = "route_types"
    __table_args__ = {"schema": "CW2"}
    route_type_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    route_type_name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))


class RouteTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = RouteType
        load_instance = True


class Difficulty(db.Model):
    __tablename__ = "difficulties"
    __table_args__ = {"schema": "CW2"}
    difficulty_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    difficulty_name = db.Column(db.String(50), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))


class DifficultySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Difficulty
        load_instance = True


class TrailTag(db.Model):
    __tablename__ = "trail_tags"
    __table_args__ = {"schema": "CW2"}
    trail_tag_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    trail_tag_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))


class TrailTagSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrailTag
        load_instance = True


trail_trailtags = db.Table(
    "trail_trailtags",
    db.Model.metadata,
    db.Column("trail_trailtag_id", db.BigInteger, primary_key=True, autoincrement=True),
    db.Column("trail_id", db.BigInteger, db.ForeignKey("CW2.trails.trail_id", ondelete="CASCADE")),
    db.Column("trail_tag_id", db.BigInteger, db.ForeignKey("CW2.trail_tags.trail_tag_id", ondelete="CASCADE")),
    schema="CW2"
)


class Waypoint(db.Model):
    __tablename__ = "waypoints"
    __table_args__ = {"schema": "CW2"}
    waypoint_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    trail_id = db.Column(db.BigInteger, db.ForeignKey("CW2.trails.trail_id", ondelete="CASCADE"), nullable=False)
    waypoint_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    latitude = db.Column(db.Numeric(9,6), nullable=False)
    longitude = db.Column(db.Numeric(9,6), nullable=False)
    sequence_no = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

class WaypointSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Waypoint
        load_instance = True
        include_fk = True


class Activity(db.Model):
    __tablename__ = "activities"
    __table_args__ = {"schema": "CW2"}

    activity_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("CW2.users.user_id"), nullable=False)
    trail_id = db.Column(db.BigInteger, db.ForeignKey("CW2.trails.trail_id"), nullable=False)

    length = db.Column(db.Numeric(7,2))
    elevation_gain = db.Column(db.Numeric(7,2))
    moving_time = db.Column(db.Integer)
    total_time = db.Column(db.Integer)
    calories = db.Column(db.Integer)
    avg_pace = db.Column(db.Numeric(5,2))
    notes = db.Column(db.Text)
    rating = db.Column(db.Integer)
    visibility = db.Column(db.String(10), default="public")

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

    user = db.relationship("User", backref="activities")

class ActivitySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Activity
        load_instance = True
        include_fk = True

    user_id = fields.Int(required=True)
    trail_id = fields.Int(required=True)
    notes = fields.Str(validate=validate.Length(max=500))
    rating = fields.Int(validate=validate.Range(min=1, max=5))
    visibility = fields.Str(validate=validate.OneOf(["public", "private", "friends"]), missing="public")
    length = fields.Float(validate=validate.Range(min=0), required=True)
    elevation_gain = fields.Float(validate=validate.Range(min=0))
    moving_time = fields.Int(validate=validate.Range(min=0), required=True)
    total_time = fields.Int(validate=validate.Range(min=0), required=True)
    calories = fields.Int(validate=validate.Range(min=0))
    avg_pace = fields.Float(validate=validate.Range(min=0))


class Photo(db.Model):
    __tablename__ = "photos"
    __table_args__ = {"schema": "CW2"}

    photo_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("CW2.users.user_id"), nullable=False)
    activity_id = db.Column(db.BigInteger, db.ForeignKey("CW2.activities.activity_id", ondelete="CASCADE"), nullable=True)
    trail_id = db.Column(db.BigInteger, db.ForeignKey("CW2.trails.trail_id", ondelete="CASCADE"), nullable=True)
    
    photo_url = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

    user = db.relationship("User", backref="photos")
    activity = db.relationship("Activity", backref="photos")

class PhotoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Photo
        load_instance = True
        include_fk = True


class UserList(db.Model):
    __tablename__ = "user_lists"
    __table_args__ = {"schema": "CW2"}

    user_list_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("CW2.users.user_id"), nullable=False)
    trail_id = db.Column(db.BigInteger, db.ForeignKey("CW2.trails.trail_id"), nullable=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    visibility = db.Column(db.String(20), nullable=False, default="public")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

    user = db.relationship("User", backref="user_lists")

class UserListSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = UserList
        load_instance = True
        include_fk = True

    name = fields.String(required=True, validate=validate.Length(max=100))
    visibility = fields.String(required=True, validate=validate.OneOf(["public", "private", "friends"]))
    
    user_id = fields.Integer(required=True)
    trail_id = fields.Integer(allow_none=True)



class Trail(db.Model):
    __tablename__ = "trails"
    __table_args__ = {"schema": "CW2"}
    trail_id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    trail_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    length = db.Column(db.Numeric(7,2), nullable=False)
    elevation_gain = db.Column(db.Float)
    estimated_time = db.Column(db.Numeric(4,2))
    route_type_id = db.Column(db.BigInteger, db.ForeignKey("CW2.route_types.route_type_id"), nullable=False)
    difficulty_id = db.Column(db.BigInteger, db.ForeignKey("CW2.difficulties.difficulty_id"), nullable=False)
    location_id = db.Column(db.BigInteger, db.ForeignKey("CW2.locations.location_id"), nullable=False)
    created_by = db.Column(db.BigInteger, db.ForeignKey("CW2.users.user_id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))
    updated_by = db.Column(db.BigInteger)
    updated_at = db.Column(db.DateTime, onupdate=lambda: datetime.now(pytz.timezone('Asia/Kuala_Lumpur')))

    waypoints = db.relationship("Waypoint", backref="trail", cascade="all, delete, delete-orphan", order_by="Waypoint.sequence_no")
    tags = db.relationship("TrailTag", secondary=trail_trailtags, backref="trails")
    location = db.relationship("Location", backref="trails")
    creator = db.relationship("User", backref="created_trails")
    route_type = db.relationship("RouteType", backref="trails")
    difficulty = db.relationship("Difficulty", backref="trails")
    activities = db.relationship("Activity", backref="parent_trail", cascade="all, delete", lazy=True)
    user_lists = db.relationship("UserList", backref="parent_trail", cascade="all, delete", lazy=True)
    photos = db.relationship("Photo", backref="trail", cascade="all, delete-orphan") 

class TrailSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Trail
        load_instance = True
        include_fk = True
        include_relationships = True

    trail_name = fields.Str(required=True, validate=validate.Length(max=100))
    description = fields.Str(validate=validate.Length(max=1000))
    length = fields.Float(required=True, validate=validate.Range(min=0))
    elevation_gain = fields.Float(validate=validate.Range(min=0))
    estimated_time = fields.Float(validate=validate.Range(min=0))
    route_type_id = fields.Int(required=True)
    difficulty_id = fields.Int(required=True)
    location_id = fields.Int(required=True)
    created_by = fields.Int(required=True)
    updated_by = fields.Int()

    waypoints = fields.Nested(WaypointSchema, many=True)
    tags = fields.Nested(TrailTagSchema, many=True)
    location = fields.Nested(LocationSchema)
    creator = fields.Nested(UserSchema)

trail_schema = TrailSchema()
trails_schema = TrailSchema(many=True)


class TrailFullDetails(db.Model):
    __tablename__ = "v_trail_full_details"
    __table_args__ = {"schema": "CW2"}
    __mapper_args__ = {"primary_key": ["trail_id"]} 

    trail_id = db.Column(db.BigInteger, primary_key=True)
    trail_name = db.Column(db.String(100))
    description = db.Column(db.Text)
    length = db.Column(db.Numeric(7,2))
    route_type = db.Column(db.String(50))
    difficulty = db.Column(db.String(50))
    location = db.Column(db.String(100))
    created_by = db.Column(db.String(50))
    user_lists = db.Column(db.String)
    tags = db.Column(db.String)
    total_activities = db.Column(db.Integer)
    avg_rating = db.Column(db.Float)
    total_photos = db.Column(db.Integer)
    total_waypoints = db.Column(db.Integer)


class TrailFullDetailsSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TrailFullDetails
        load_instance = True

trail_full_schema = TrailFullDetailsSchema()
trails_full_schema = TrailFullDetailsSchema(many=True)
