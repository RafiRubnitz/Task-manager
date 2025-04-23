# app/models/user.py
from app import mongo,bcrypt, login_manager

from flask_login import UserMixin
from bson.objectid import ObjectId


class User(UserMixin):
    def __init__(self, username, email, password_hash=None, _id=None):
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self._id = _id if _id else ObjectId() # Generate ObjectId if not provided

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        # Ensure password_hash is bytes for bcrypt comparison
        stored_hash = self.password_hash
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        return bcrypt.check_password_hash(stored_hash, password)

    def save(self):
        collection = mongo.db.users # Access collection here
        user_data = {
            "_id": self._id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash
        }
        # Use update_one with upsert=True to insert or update
        collection.update_one({'_id': self._id}, {'$set': user_data}, upsert=True)

    def get_id(self):
        """Required by Flask-Login. Returns the user's ID as a string."""
        return str(self._id)

    @staticmethod
    def get(user_id):
        """Required by Flask-Login's user_loader. Fetches a user by their ID."""
        collection = mongo.db.users # Access collection here
        try:
            user_data = collection.find_one({"_id": ObjectId(user_id)})
            if user_data:
                return User(
                    _id=user_data['_id'],
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=user_data['password_hash']
                )
        except Exception as e:
            # Handle potential errors like invalid ObjectId format
            print(f"Error getting user by ID: {e}")
            return None
        return None

    @staticmethod
    def find_by_username(username):
        collection = mongo.db.users # Access collection here
        user_data = collection.find_one({"username": username})
        if user_data:
            return User(
                _id=user_data['_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash']
            )
        return None

    @staticmethod
    def find_by_email(email):
        collection = mongo.db.users # Access collection here
        user_data = collection.find_one({"email": email})
        if user_data:
            return User(
                _id=user_data['_id'],
                username=user_data['username'],
                email=user_data['email'],
                password_hash=user_data['password_hash']
            )
        return None 