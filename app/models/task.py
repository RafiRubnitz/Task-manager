# app/models/task.py
from app import mongo
from bson.objectid import ObjectId
from datetime import datetime

class Task:
    def __init__(self, user_id, original_text, category, summary, details=None, created_at=None, _id=None):
        self._id = _id if _id else ObjectId()
        self.user_id = ObjectId(user_id) # Ensure user_id is stored as ObjectId
        self.original_text = original_text
        self.category = category # e.g., "Shopping List", "Schedule", "Notes", "Long-Term Tasks"
        self.summary = summary
        self.details = details if details is not None else {} # e.g., {"date": "...", "time": "...", "items": [...]}
        self.created_at = created_at if created_at else datetime.utcnow()

    def save(self):
        collection = mongo.db.tasks # Access collection here
        task_data = {
            "_id": self._id,
            "user_id": self.user_id,
            "original_text": self.original_text,
            "category": self.category,
            "summary": self.summary,
            "details": self.details,
            "created_at": self.created_at
        }
        # Use update_one with upsert=True to insert or update
        collection.update_one({'_id': self._id}, {'$set': task_data}, upsert=True)

    @staticmethod
    def find_by_user(user_id):
        """Find all tasks for a given user."""
        collection = mongo.db.tasks # Access collection here
        # Ensure user_id is ObjectId for querying
        if isinstance(user_id, str):
             user_id = ObjectId(user_id)
        return list(collection.find({"user_id": user_id}).sort("created_at", -1)) # Sort by newest first

    @staticmethod
    def find_by_id(task_id):
        """Find a specific task by its ID."""
        collection = mongo.db.tasks # Access collection here
        try:
            return collection.find_one({"_id": ObjectId(task_id)})
        except Exception:
             return None # Handle invalid ObjectId

    @classmethod
    def from_dict(cls, data):
        """Create a Task instance from a dictionary (e.g., from MongoDB)."""
        return cls(
            _id=data.get('_id'),
            user_id=data.get('user_id'),
            original_text=data.get('original_text'),
            category=data.get('category'),
            summary=data.get('summary'),
            details=data.get('details'),
            created_at=data.get('created_at')
        )

    def update(self, updates):
        """Update specific fields of the task."""
        collection = mongo.db.tasks # Access collection here
        # Only allow updating certain fields
        allowed_updates = {'original_text', 'category', 'summary', 'details'}
        update_data = {k: v for k, v in updates.items() if k in allowed_updates}
        if update_data:
            collection.update_one({'_id': self._id}, {'$set': update_data})
            # Update instance attributes as well
            for k, v in update_data.items():
                setattr(self, k, v)

    @staticmethod
    def delete(task_id):
        """Delete a task by its ID."""
        collection = mongo.db.tasks # Access collection here
        try:
             result = collection.delete_one({"_id": ObjectId(task_id)})
             return result.deleted_count > 0 # Return True if deleted, False otherwise
        except Exception:
             return False # Handle invalid ObjectId or other errors 