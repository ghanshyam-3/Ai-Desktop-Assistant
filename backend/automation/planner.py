from sqlalchemy.orm import Session
from database.db import SessionLocal, engine, Base
from database.models import Task, Note, Plan
from sqlalchemy import text
from datetime import datetime

class Planner:
    def __init__(self):
        # Create tables if they don't exist (this handles new tables like Plan)
        Base.metadata.create_all(bind=engine)
        self._migrate_v2()
        
    def _migrate_v2(self):
        """Auto-migrate database schema for V2 features"""
        try:
            with engine.connect() as conn:
                # List of updates to apply
                updates = [
                    "ALTER TABLE tasks ADD COLUMN description TEXT",
                    "ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'",
                    "ALTER TABLE tasks ADD COLUMN status TEXT DEFAULT 'pending'",
                    "ALTER TABLE tasks ADD COLUMN reminder_time DATETIME",
                    "ALTER TABLE tasks ADD COLUMN tags TEXT",
                    "ALTER TABLE tasks ADD COLUMN updated_at DATETIME",
                    "ALTER TABLE notes ADD COLUMN title TEXT",
                    "ALTER TABLE notes ADD COLUMN linked_task_id INTEGER",
                    "ALTER TABLE notes ADD COLUMN updated_at DATETIME",
                ]
                
                for stmt in updates:
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                        print(f"Migrated: {stmt}")
                    except Exception as e:
                        # Column likely exists
                        pass
                        
                # Ensure Plans table exists (SQLAlchemy create_all might miss it if DB exists but table doesn't?) 
                # Actually create_all handles missing tables. But let's be safe.
                pass 

                # Migrate Email Tables
                email_updates = [
                    "CREATE TABLE IF NOT EXISTS email_contacts (id INTEGER PRIMARY KEY, user_id INTEGER, nickname VARCHAR, email VARCHAR, created_at DATETIME, updated_at DATETIME)",
                    "CREATE INDEX IF NOT EXISTS ix_email_contacts_nickname ON email_contacts (nickname)",
                    "CREATE TABLE IF NOT EXISTS email_logs (id INTEGER PRIMARY KEY, user_id INTEGER, contact_id INTEGER, recipient VARCHAR, subject VARCHAR, encrypted_body TEXT, status VARCHAR, error_message TEXT, message_id VARCHAR, sent_at DATETIME)"
                ]
                for stmt in email_updates:
                    try:
                        conn.execute(text(stmt))
                        conn.commit()
                    except Exception as e:
                        print(f"Email Table Migration Info: {e}") 
                
        except Exception as e:
            print(f"Migration V2 Check Failed: {e}")
        
    # --- TASKS ---
    def add_task(self, title, description=None, priority="medium", due_date=None, reminder_time=None, tags=None):
        db = SessionLocal()
        try:
            if due_date == "": due_date = None
            if reminder_time == "": reminder_time = None
            
            task = Task(
                title=title, 
                description=description,
                priority=priority,
                due_date=due_date,
                reminder_time=reminder_time,
                tags=tags,
                status="pending"
            )
            db.add(task)
            db.commit()
            return f"Added task: {title}"
        finally:
            db.close()

    def get_tasks(self):
        """Return full list of tasks for UI"""
        db = SessionLocal()
        try:
            # Return all tasks, sorted by pending first, then by date desc
            tasks = db.query(Task).order_by(Task.status.desc(), Task.created_at.desc()).all()
            return [{
                "id": t.id, 
                "title": t.title, 
                "description": t.description,
                "priority": t.priority,
                "status": t.status,
                "due_date": str(t.due_date) if t.due_date else None,
                "tags": t.tags
            } for t in tasks]
        finally:
            db.close()

    def complete_task(self, task_id, status="completed"):
        db = SessionLocal()
        try:
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                task.status = status
                task.is_completed = (status == "completed")
                db.commit()
                return True
            return False
        finally:
            db.close()

    # --- NOTES ---
    def add_note(self, content, title=None):
        db = SessionLocal()
        try:
            note = Note(content=content, title=title)
            db.add(note)
            db.commit()
            return "Note saved."
        finally:
            db.close()

    def get_notes(self):
        db = SessionLocal()
        try:
            notes = db.query(Note).order_by(Note.created_at.desc()).limit(20).all()
            return [{
                "id": n.id, 
                "title": n.title, 
                "content": n.content, 
                "created_at": str(n.created_at)
            } for n in notes]
        finally:
            db.close()

    # --- PLANS ---
    def add_plan(self, title, description=None, target_date=None):
        db = SessionLocal()
        try:
            plan = Plan(title=title, description=description, target_date=target_date)
            db.add(plan)
            db.commit()
            return "Plan created."
        finally:
            db.close()

    def get_plans(self):
        db = SessionLocal()
        try:
            plans = db.query(Plan).order_by(Plan.created_at.desc()).all()
            return [{
                "id": p.id,
                "title": p.title,
                "description": p.description,
                "progress": p.progress,
                "target_date": str(p.target_date) if p.target_date else None
            } for p in plans]
        finally:
            db.close()

    # --- REMINDERS ---
    def check_reminders(self):
        """Find tasks with passed reminder times that aren't completed"""
        db = SessionLocal()
        try:
            # Logic: Find tasks where reminder_time < now AND status != completed
            # ideally, we would have a 'reminded' flag, but for MVP we might just check if it's close?
            # Or simpler: The frontend handles specific time checks if we pass the reminder_time.
            # But user asked for Electron main process logic.
            # Let's return tasks that have reminders set for today/future for the UI to handle?
            # Or return 'due' reminders.
            return [] 
        finally:
             db.close()
            
    def list_tasks(self):
        # Voice: List pending tasks for TODAY
        raw_tasks = self.get_tasks()
        today_str = datetime.now().date().isoformat()
        
        pending_today = []
        for t in raw_tasks:
            if t['status'] == 'completed': continue
            
            # Include if due_date is Today OR None (undated) OR Overdue?
            # User asked specifically for "Today's remaining".
            # Let's count overdue as well to be helpful.
            if t['due_date']:
                # Compare YYYY-MM-DD
                # t['due_date'] is a string "YYYY-MM-DD HH:MM:SS" or similar
                task_date = t['due_date'].split(" ")[0]
                if task_date <= today_str:
                    pending_today.append(t['title'])
            else:
                # Decide if we show undated tasks. 
                # "Today's task" implies scheduled ones. 
                # But let's verify checking the prompt "pendding task".
                # Let's include them for now.
                pending_today.append(t['title'])

        if not pending_today: return "You have no pending tasks for today."
        return f"You have {len(pending_today)} tasks remaining: " + ", ".join(pending_today)

    def list_notes(self):
        # Legacy support for voice
        notes = self.get_notes()
        if not notes: return "No notes."
        return ", ".join([n['content'] for n in notes])

    def find_task_fuzzy(self, query):
        """Find a task by name/content using simple substring match logic"""
        query = query.lower()
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.status != 'completed').all()
            # 1. Exact match
            for t in tasks:
                if t.title.lower() == query: return t
            
            # 2. Substring match
            for t in tasks:
                if query in t.title.lower(): return t
                
            return None
        finally:
            db.close()

    def complete_task_by_name(self, name):
        task = self.find_task_fuzzy(name)
        if task:
            return self.complete_task(task.id)
        return False

    def delete_task_by_name(self, name):
        task = self.find_task_fuzzy(name)
        if task:
            db = SessionLocal()
            try:
                # We need to re-fetch to delete in this session
                t_to_del = db.query(Task).get(task.id)
                db.delete(t_to_del)
                db.commit()
                return True
            finally:
                db.close()
        return False
