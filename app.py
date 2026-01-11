import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash
import db
import gemini_service

app = Flask(__name__)
app.secret_key = 'myvibesaas_secret_key'

@app.context_processor
def inject_user_data():
    """Injects tier and user info into all templates for theming"""
    if 'user_id' in session:
        return {'user_name': session.get('user_name'), 'tier': session.get('tier', 'free')}
    return {}

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('check_tier_redirect'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_name = request.form.get('user_name').strip()
    if not user_name: return redirect(url_for('index'))

    user = db.get_user_by_name(user_name)
    
    if user:
        session['user_id'] = user['user_id']
        session['user_name'] = user['user_name']
        session['tier'] = user.get('tier', 'free') # Handle legacy users
    else:
        # Create new user
        new_id = str(uuid.uuid4())
        if db.create_user(new_id, user_name):
            session['user_id'] = new_id
            session['user_name'] = user_name
            session['tier'] = 'free'
        else:
            flash("Error creating user", "danger")
            return redirect(url_for('index'))

    return redirect(url_for('check_tier_redirect'))

@app.route('/check_redirect')
def check_tier_redirect():
    """Decides where to send the user based on tier"""
    tier = session.get('tier', 'free')
    
    # Requirement: If 'free', show subscription page first
    if tier == 'free':
        return redirect(url_for('subscription'))
    
    # Otherwise, go to default app (To-Do)
    return redirect(url_for('todo_dashboard'))

@app.route('/subscription', methods=['GET', 'POST'])
def subscription():
    if 'user_id' not in session: return redirect(url_for('index'))
    
    if request.method == 'POST':
        selected_tier = request.form.get('tier')
        if selected_tier in ['free', 'standard', 'plus']:
            db.update_user_tier(session['user_id'], selected_tier)
            session['tier'] = selected_tier
            
            # If they chose free, just continue. If paid, we pretend they paid.
            flash(f"You are now on the {selected_tier.capitalize()} plan!", "success")
            return redirect(url_for('todo_dashboard'))
            
    return render_template('subscription.html', current_tier=session.get('tier'))

# --- APP ROUTES ---

@app.route('/todo')
def todo_dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    data = db.get_user_lists_with_tasks(session['user_id'])
    return render_template('todo.html', todo_data=data, active_tab='todo')

@app.route('/stash')
def stash_dashboard():
    if 'user_id' not in session: return redirect(url_for('index'))
    stashes = db.get_user_stashes(session['user_id'])
    return render_template('stash.html', stashes=stashes, active_tab='stash')

# --- LOGIC ROUTES (POST) ---

@app.route('/create_list', methods=['POST'])
def create_list():
    title = request.form.get('list_title')
    subtasks = gemini_service.generate_subtasks(title)
    
    list_id = str(uuid.uuid4())
    tasks_to_save = [(str(uuid.uuid4()), desc) for desc in subtasks]
    db.save_list_and_tasks(session['user_id'], list_id, title, tasks_to_save)
    return redirect(url_for('todo_dashboard'))

@app.route('/stash_url', methods=['POST'])
def stash_url():
    url = request.form.get('url_link')
    ai_res = gemini_service.summarize_content(url)
    db.save_stash(str(uuid.uuid4()), session['user_id'], url, ai_res['summary'], ai_res['tags'])
    return redirect(url_for('stash_dashboard'))

# Reusing delete logic from before, mapped to new file structure
@app.route('/delete_list/<id>', methods=['POST'])
def remove_list(id):
    db.delete_list(id)
    return redirect(url_for('todo_dashboard'))

@app.route('/delete_task/<id>', methods=['POST'])
def remove_task(id):
    db.delete_task(id)
    return redirect(url_for('todo_dashboard'))

@app.route('/toggle_task/<id>', methods=['POST'])
def toggle_task(id):
    is_completed = True if request.form.get('is_completed') == 'true' else False
    db.toggle_task_status(id, is_completed)
    return redirect(url_for('todo_dashboard'))

@app.route('/delete_stash/<id>', methods=['POST'])
def remove_stash(id):
    db.delete_stash(id)
    return redirect(url_for('stash_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)