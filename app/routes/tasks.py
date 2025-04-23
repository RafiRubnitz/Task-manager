# app/routes/tasks.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models.task import Task
# Placeholder for Gemini client import
from gemini.client import classify_task
import json # For potential JSON parsing if Gemini returns string

bp = Blueprint('tasks', __name__)

CATEGORIES = ["Shopping List", "Schedule", "Notes", "Long-Term Tasks", "Uncategorized"]

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    user_tasks_cursor = Task.collection.find({"user_id": current_user._id}).sort("created_at", -1)
    tasks_by_category = {category: [] for category in CATEGORIES}
    for task_data in user_tasks_cursor:
        # task = Task.from_dict(task_data) # Convert dict to Task object if needed, or just use the dict
        category = task_data.get('category', 'Uncategorized')
        if category in tasks_by_category:
            tasks_by_category[category].append(task_data) # Append the raw dictionary
        else:
            tasks_by_category['Uncategorized'].append(task_data) # Fallback for unexpected categories

    return render_template('dashboard.html', tasks_by_category=tasks_by_category, categories=CATEGORIES)

@bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task_text = request.form.get('task_text')
    if not task_text:
        flash('Task text cannot be empty.', 'warning')
        return redirect(url_for('tasks.dashboard'))

    # --- Placeholder for Gemini Integration ---
    try:
        # TODO: Replace with actual Gemini API call
        classified_data = classify_task(task_text, current_app.config['GEMINI_API_KEY'])

        # Dummy data for now:
        # classified_data = {
        #     "category": "Notes", # Default or determined logic
        #     "summary": task_text[:50] + "..." if len(task_text) > 50 else task_text, # Simple summary
        #     "details": {}
        # }
        # Example of assigning category based on keywords (very basic, Gemini should do this)
        if "buy" in task_text.lower() or "milk" in task_text.lower() or "eggs" in task_text.lower():
             classified_data["category"] = "Shopping List"
        elif "meeting" in task_text.lower() or "appointment" in task_text.lower() or " at " in task_text.lower():
             classified_data["category"] = "Schedule"
        elif len(task_text) > 100: # Arbitrary length for long-term
             classified_data["category"] = "Long-Term Tasks"

        if classified_data['category'] not in CATEGORIES:
             classified_data['category'] = 'Uncategorized'

    except Exception as e:
        flash(f'Error classifying task: {e}. Task saved as Uncategorized.', 'danger')
        # Fallback data
        classified_data = {
            "category": "Uncategorized",
            "summary": task_text[:50] + "..." if len(task_text) > 50 else task_text,
            "details": {}
        }
    # --- End Placeholder ---

    # Save the task
    new_task = Task(
        user_id=current_user.get_id(),
        original_text=task_text,
        category=classified_data.get('category', 'Uncategorized'),
        summary=classified_data.get('summary', 'No summary provided'),
        details=classified_data.get('details', {})
    )
    new_task.save()

    flash('Task added successfully!', 'success')
    return redirect(url_for('tasks.dashboard'))

@bp.route('/edit_task/<task_id>', methods=['POST'])
@login_required
def edit_task(task_id):
    task = Task.find_by_id(task_id)
    if not task or task['user_id'] != current_user._id:
        flash('Task not found or you do not have permission to edit it.', 'danger')
        return redirect(url_for('tasks.dashboard'))

    # Get updated data from form
    updated_data = {
        'original_text': request.form.get('original_text', task.get('original_text')),
        'summary': request.form.get('summary', task.get('summary')),
        'category': request.form.get('category', task.get('category')),
        # Potentially update details as well, might need more complex form handling
        # 'details': json.loads(request.form.get('details', '{}')) # Example if details are sent as JSON string
    }

    # Validate category
    if updated_data['category'] not in CATEGORIES:
        flash(f"Invalid category specified. Setting to 'Uncategorized'.", 'warning')
        updated_data['category'] = 'Uncategorized'

    # Use the update method from the Task model
    # We need the _id which is already part of the task dict fetched by find_by_id
    task_obj = Task.from_dict(task) # Create instance to use update method easily
    task_obj.update(updated_data)

    flash('Task updated successfully!', 'success')
    return redirect(url_for('tasks.dashboard'))


@bp.route('/delete_task/<task_id>', methods=['POST']) # Use POST for deletion
@login_required
def delete_task(task_id):
    task = Task.find_by_id(task_id)
    # Ensure task exists and belongs to the current user
    if not task or task['user_id'] != current_user._id:
        flash('Task not found or you do not have permission to delete it.', 'danger')
        # Return a 403 Forbidden or 404 Not Found status perhaps?
        # For now, just redirect
        return redirect(url_for('tasks.dashboard'))

    if Task.delete(task_id):
        flash('Task deleted successfully!', 'success')
    else:
        flash('Error deleting task.', 'danger')

    return redirect(url_for('tasks.dashboard')) 