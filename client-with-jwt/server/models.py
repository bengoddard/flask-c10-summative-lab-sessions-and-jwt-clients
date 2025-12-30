from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from marshmallow import Schema, fields, validate
from config import db, bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    _password_hash = db.Column(db.String)
    bio = db.Column(db.String)

    entries = db.relationship('Entry', back_populates='user')

    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')

    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(
            password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')

    def authenticate(self, password):
        return bcrypt.check_password_hash(
            self._password_hash, password.encode('utf-8'))

    def __repr__(self):
        return f'<User {self.username}>'

class Entry(db.Model):
    __tablename__ = 'entries'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False)
    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates="entries")

    @validates('content')
    def validate_instructions(self, key, content):
        if not content:
            raise ValueError("Content must be present.")
        if len(content) < 25:
            raise ValueError("Content must be at least 25 characters long.")
        return content

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(required=True)
    bio = fields.Str()
    password = fields.Str(load_only=True, required=True)

    entries = fields.List(fields.Nested(lambda: EntrySchema(exclude=("user",))))


class EntrySchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True)
    content = fields.Str(
        required=True,
        validate=validate.Length(min=25, error="Content must be at least 25 characters long.")
    )
    user_id = fields.Int()
    user = fields.Nested(UserSchema(exclude=("entries",)))
