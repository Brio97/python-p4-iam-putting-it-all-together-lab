from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    _password_hash = db.Column(db.String(128), nullable=True)  # Password can be null
    image_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.String(500), nullable=True)

    # Relationship with recipes
    recipes = relationship('Recipe', backref='user', lazy=True)

    # Password management using bcrypt
    @hybrid_property
    def password_hash(self):
        raise AttributeError("Password is not a readable attribute")

    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    # Validation for username presence and uniqueness
    @validates('username')
    def validate_username(self, key, username):
        if not username or username.strip() == '':
            raise ValueError("Username must be present")
        return username

    # Authenticate user with username and password
    def authenticate(self, password):
        # Ensure that password is provided
        if not password:
            return False
        
        # Verify the password
        return bcrypt.check_password_hash(self._password_hash, password)

    # Custom serialization method to prevent deep recursion
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'image_url': self.image_url,
            'bio': self.bio,
            'recipes': [recipe.to_dict() for recipe in self.recipes]  # Custom serialization of related recipes
        }

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    instructions = Column(String, nullable=False)
    minutes_to_complete = Column(Integer)

    # Foreign key to link with User, nullable to allow flexibility
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Validations for Recipe fields
    @validates('title')
    def validate_title(self, key, title):
        if not title or title.strip() == '':
            raise ValueError("Title must be present")
        return title

    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long")
        return instructions

    # Custom serialization method to prevent deep recursion
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'instructions': self.instructions,
            'minutes_to_complete': self.minutes_to_complete,
            'user_id': self.user_id  # Optionally include related user data if needed
        }
