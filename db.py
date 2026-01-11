import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# --- User & Tier Management ---
def get_user_by_name(user_name):
    conn = get_db_connection()
    if not conn: return None
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # We try to fetch the tier column. If it doesn't exist yet in DB, this might error if not migrated.
        cur.execute("SELECT * FROM public.users WHERE user_name = %s", (user_name,))
        user = cur.fetchone()
        cur.close()
        conn.close()
        return user
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def create_user(user_id, user_name):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        # Default tier is 'free'
        cur.execute("INSERT INTO public.users (user_id, user_name, tier) VALUES (%s, %s, 'free')", (user_id, user_name))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False

def update_user_tier(user_id, new_tier):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("UPDATE public.users SET tier = %s WHERE user_id = %s", (new_tier, user_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating tier: {e}")
        return False

# --- To-Do App Functions ---
def save_list_and_tasks(user_id, list_id, list_name, tasks_data):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO public.todolists (list_id, user_id, list_name) VALUES (%s, %s, %s)", (list_id, user_id, list_name))
        for task_id, desc in tasks_data:
            cur.execute("INSERT INTO public.tasks (task_id, list_id, task_description, is_completed) VALUES (%s, %s, %s, %s)", (task_id, list_id, desc, False))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        if conn: conn.rollback()
        return False

def get_user_lists_with_tasks(user_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM public.todolists WHERE user_id = %s", (user_id,))
        lists = cur.fetchall()
        result = []
        for lst in lists:
            cur.execute("SELECT * FROM public.tasks WHERE list_id = %s ORDER BY task_description", (lst['list_id'],))
            tasks = cur.fetchall()
            result.append({'list_id': lst['list_id'], 'list_name': lst['list_name'], 'tasks': tasks})
        cur.close()
        conn.close()
        return result
    except Exception as e:
        return []

def delete_list(list_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM public.tasks WHERE list_id = %s", (list_id,))
        cur.execute("DELETE FROM public.todolists WHERE list_id = %s", (list_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except: return False

def delete_task(task_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM public.tasks WHERE task_id = %s", (task_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except: return False

def toggle_task_status(task_id, is_completed):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("UPDATE public.tasks SET is_completed = %s WHERE task_id = %s", (is_completed, task_id))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except: return False

# --- Stash App Functions ---
def save_stash(url_id, user_id, url, summary, tags):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("INSERT INTO public.stashed_urls (url_id, user_id, url, summary, tags) VALUES (%s, %s, %s, %s, %s)", (url_id, user_id, url, summary, tags))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except: return False

def get_user_stashes(user_id):
    conn = get_db_connection()
    if not conn: return []
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM public.stashed_urls WHERE user_id = %s", (user_id,))
        stashes = cur.fetchall()
        cur.close()
        conn.close()
        return stashes
    except: return []

def delete_stash(url_id):
    conn = get_db_connection()
    if not conn: return False
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM public.stashed_urls WHERE url_id = %s", (url_id,))
        conn.commit()
        cur.close()
        conn.close()
        return True
    except: return False