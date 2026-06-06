import os
import sys
import time
import datetime
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer
from utils import BaseHandler, SessionStore, load_json, save_json, hash_password, get_translations, get_available_languages, get_translated_message, get_active_questions_file, get_available_questions_files

# Initialize in-memory session store for admin
admin_sessions = SessionStore(expiry_seconds=1800)

COMMON_CSS = """
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:ital,wght@0,300;0,400;0,500;0,600;0,700;1,300;1,400;1,500;1,600;1,700&display=swap');

:root {
  --bg: #0f0f0f;
  --surface: #1a1a1a;
  --surface-hover: #262626;
  --accent: #f59e0b;
  --accent-hover: #d97706;
  --text: #e5e5e5;
  --text-muted: #a3a3a3;
  --error: #ef4444;
  --success: #22c55e;
  --border: #333333;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: 'IBM Plex Mono', monospace;
  background-color: var(--bg);
  color: var(--text);
  line-height: 1.5;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

header {
  background-color: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--accent);
}

.nav-links {
  display: flex;
  gap: 1.5rem;
  margin-left: 2rem;
  flex: 1;
}

.nav-links a {
  font-size: 0.9rem;
  color: var(--text-muted);
  font-weight: 500;
}

.nav-links a.active, .nav-links a:hover {
  color: var(--accent);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-badge {
  background: var(--surface-hover);
  border: 1px solid var(--border);
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.logout-link {
  color: var(--error);
  font-size: 0.85rem;
  border: 1px solid var(--error);
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.logout-link:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #fff;
}

h1, h2, h3 {
  font-weight: 600;
  color: #fff;
  margin-bottom: 1.25rem;
}

a {
  color: var(--accent);
  text-decoration: none;
  transition: color 0.2s ease;
}

a:hover {
  color: var(--accent-hover);
}

.container {
  max-width: 1000px;
  margin: 2rem auto;
  padding: 0 1rem;
  width: 100%;
  flex: 1;
}

.card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  margin-bottom: 1.5rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.metric-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.metric-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.metric-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--accent);
  margin-top: 0.5rem;
}

.btn {
  display: inline-block;
  background-color: var(--accent);
  color: #000;
  font-weight: 700;
  font-family: inherit;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
}

.btn:hover {
  background-color: var(--accent-hover);
}

.btn-secondary {
  background-color: transparent;
  color: var(--text);
  border: 1px solid var(--border);
}

.btn-secondary:hover {
  background-color: var(--surface-hover);
  color: #fff;
}

.btn-danger {
  background-color: var(--error);
  color: #fff;
}

.btn-danger:hover {
  background-color: #dc2626;
}

.input-group {
  margin-bottom: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

label.input-label {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-muted);
}

input[type="text"],
input[type="password"],
input[type="number"],
textarea,
select {
  background-color: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  font-family: inherit;
  padding: 0.75rem;
  border-radius: 4px;
  width: 100%;
  transition: border-color 0.2s;
}

input:focus, textarea:focus, select:focus {
  outline: none;
  border-color: var(--accent);
}

.alert {
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1.5rem;
  border: 1px solid transparent;
  font-size: 0.9rem;
}

.alert-success {
  background-color: rgba(34, 197, 94, 0.1);
  border-color: var(--success);
  color: var(--success);
}

.alert-error {
  background-color: rgba(239, 68, 68, 0.1);
  border-color: var(--error);
  color: var(--error);
}

table {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
}

th, td {
  padding: 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}

th {
  background-color: var(--surface-hover);
  color: #fff;
  font-weight: 600;
  text-transform: uppercase;
  font-size: 0.8rem;
  letter-spacing: 0.05em;
}

tr:hover td {
  background-color: rgba(255, 255, 255, 0.02);
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-success {
  background: rgba(34, 197, 94, 0.2);
  color: var(--success);
  border: 1px solid var(--success);
}

.badge-error {
  background: rgba(239, 68, 68, 0.2);
  color: var(--error);
  border: 1px solid var(--error);
}

.badge-warning {
  background: rgba(245, 158, 11, 0.2);
  color: var(--accent);
  border: 1px solid var(--accent);
}

footer {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  font-size: 0.8rem;
  border-top: 1px solid var(--border);
  background: var(--surface);
  margin-top: auto;
}
"""

class AdminAppHandler(BaseHandler):
    """
    HTTP Request Handler for the Admin Panel application. Restricted to admin role users.
    Provides student management (add, delete, reset pass) and scorecard inspection.
    """

    def do_GET(self):
        # Load translations once per request
        self.lang_code, self.t = get_translations()

        url = urlparse(self.path)
        path = url.path
        params = parse_qs(url.query)

        # 1. Login Page
        if path == "/login":
            error_msg = params.get("error", [None])[0]
            self.show_login(error_msg)
            return

        # 2. Authenticate session
        session = self.get_session(admin_sessions)
        if not session:
            self.redirect("/login")
            return

        # 3. Logout Endpoint
        if path == "/logout":
            admin_sessions.delete(session["session_id"])
            self.set_cookie("session_id", "", max_age=-1)
            self.redirect("/login")
            return

        # Flash messages (Success/Error) from query params
        success_msg = params.get("msg", [None])[0]
        error_msg = params.get("err", [None])[0]

        # 4. Route Routing
        if path == "/":
            self.show_dashboard(session)
            return
        elif path == "/students":
            self.show_students_list(session, success_msg, error_msg)
            return
        elif path == "/students/add":
            self.show_add_student(session)
            return
        elif path == "/students/reset-password":
            username = params.get("username", [None])[0]
            if not username:
                self.redirect("/students?err=err_no_username_reset")
                return
            self.show_reset_password(session, username)
            return
        elif path == "/students/detail":
            username = params.get("username", [None])[0]
            if not username:
                self.redirect("/students?err=err_no_username_detail")
                return
            self.show_student_detail(session, username)
            return

        # 404 Page
        self.send_html("<h1>404 Not Found</h1>", status=404)

    def do_POST(self):
        # Load translations once per request
        self.lang_code, self.t = get_translations()

        url = urlparse(self.path)
        path = url.path

        # 1. Login Form Action
        if path == "/login":
            post_data = self.parse_post_body()
            username = post_data.get("username", "").strip()
            password = post_data.get("password", "")

            users = load_json("data/users.json", [])
            user = None
            for u in users:
                if u["username"] == username:
                    user = u
                    break

            if user and user["password_hash"] == hash_password(password):
                # Ensure the user has the admin role
                if user.get("role") != "admin":
                    self.redirect("/login?error=err_access_restricted")
                    return
                
                session = admin_sessions.create(username)
                self.set_cookie("session_id", session["session_id"])
                self.redirect("/")
            else:
                self.redirect("/login?error=err_invalid_credentials")
            return

        # Authenticate session for POST requests
        session = self.get_session(admin_sessions)
        if not session:
            self.redirect("/login")
            return

        # 2. Add Student Form Action
        if path == "/students/add":
            post_data = self.parse_post_body()
            username = post_data.get("username", "").strip()
            password = post_data.get("password", "")
            role = post_data.get("role", "student")

            if not username or not password:
                self.redirect("/students?err=err_empty_credentials")
                return

            users = load_json("data/users.json", [])
            for u in users:
                if u["username"].lower() == username.lower():
                    self.redirect(f"/students?err=err_user_exists:{username}")
                    return

            # Append user
            new_user = {
                "username": username,
                "password_hash": hash_password(password),
                "role": role
            }
            users.append(new_user)
            save_json("data/users.json", users)
            self.redirect(f"/students?msg=msg_user_created:{username}")
            return

        # 3. Reset Password Action
        if path == "/students/reset-password":
            post_data = self.parse_post_body()
            username = post_data.get("username", "")
            new_password = post_data.get("new_password", "")

            if not username or not new_password:
                self.redirect("/students?err=err_password_empty")
                return

            users = load_json("data/users.json", [])
            updated = False
            for u in users:
                if u["username"] == username:
                    u["password_hash"] = hash_password(new_password)
                    updated = True
                    break

            if updated:
                save_json("data/users.json", users)
                self.redirect(f"/students?msg=msg_password_reset:{username}")
            else:
                self.redirect(f"/students?err=err_user_not_found:{username}")
            return

        # 4. Delete Student Action
        if path == "/students/delete":
            post_data = self.parse_post_body()
            username = post_data.get("username", "")

            if not username:
                self.redirect("/students?err=err_no_username_delete")
                return

            users = load_json("data/users.json", [])
            
            # Find and remove
            filtered_users = [u for u in users if u["username"] != username]
            if len(filtered_users) == len(users):
                self.redirect(f"/students?err=err_user_not_found:{username}")
                return

            save_json("data/users.json", filtered_users)
            
            # Clean up scorecard file if it exists
            scorecard_path = f"data/scorecards/{username}.json"
            if os.path.exists(scorecard_path):
                try:
                    os.remove(scorecard_path)
                except OSError:
                    pass

            self.redirect(f"/students?msg=msg_user_deleted:{username}")
            return

        # 5. Save Global Settings Action
        if path == "/settings/save":
            post_data = self.parse_post_body()
            selected_lang = post_data.get("language", "en").strip()
            selected_file = post_data.get("questions_file", "question_00.json").strip()

            config = load_json("data/config.json", {})
            config["language"] = selected_lang
            config["questions_file"] = selected_file
            save_json("data/config.json", config)

            self.redirect("/?msg=msg_settings_updated")
            return

        self.send_html("<h1>404 Not Found</h1>", status=404)

    # =====================================================================
    # HTML RENDERING HELPERS
    # =====================================================================

    def render_page(self, title, active_tab, content, session):
        username = session["username"]
        admin_badge_text = self.t['admin_badge'].format(username=username)
        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{self.t.get(title, title)} - {self.t['admin_title']}</title>
    <style>{COMMON_CSS}</style>
</head>
<body>
    <header>
        <div class="header-title">{self.t['admin_title']}</div>
        <div class="nav-links">
            <a href="/" class="{ 'active' if active_tab == 'dashboard' else '' }">{self.t['nav_dashboard']}</a>
            <a href="/students" class="{ 'active' if active_tab == 'students' else '' }">{self.t['nav_students']}</a>
            <a href="/students/add" class="{ 'active' if active_tab == 'add' else '' }">{self.t['nav_add_user']}</a>
        </div>
        <div class="header-right">
            <span class="user-badge">{admin_badge_text}</span>
            <a href="/logout" class="logout-link">{self.t['logout']}</a>
        </div>
    </header>
    <div class="container">
        {content}
    </div>
    <footer>
        &copy; {datetime.datetime.now().year} {self.t['footer_text']}
    </footer>
</body>
</html>"""
        self.send_html(html)

    def show_login(self, error_msg):
        translated_err = get_translated_message(error_msg, self.t)
        error_html = f'<div class="alert alert-error">{translated_err}</div>' if error_msg else ''
        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{self.t['login_title']}</title>
    <style>{COMMON_CSS}</style>
</head>
<body>
    <header>
        <div class="header-title">{self.t['login_header']}</div>
    </header>
    <div class="container" style="max-width: 450px; margin-top: 6rem;">
        <div class="card">
            <h2 style="text-align: center; margin-bottom: 1.5rem; color: var(--accent);">{self.t['login_card_title']}</h2>
            {error_html}
            <form action="/login" method="POST">
                <div class="input-group">
                    <label class="input-label" for="username">{self.t['login_username_label']}</label>
                    <input type="text" id="username" name="username" required autocomplete="username" autofocus>
                </div>
                <div class="input-group" style="margin-bottom: 2rem;">
                    <label class="input-label" for="password">{self.t['login_password_label']}</label>
                    <input type="password" id="password" name="password" required autocomplete="current-password">
                </div>
                <button type="submit" class="btn">{self.t['login_submit']}</button>
            </form>
        </div>
    </div>
    <footer>
        &copy; {datetime.datetime.now().year} {self.t['footer_text']}
    </footer>
</body>
</html>"""
        self.send_html(html)

    def show_dashboard(self, session):
        # Gather metrics
        users = load_json("data/users.json", [])
        active_q_file = get_active_questions_file()
        questions = load_json(os.path.join("data", active_q_file), [])
        
        student_count = sum(1 for u in users if u.get("role") == "student")
        question_count = len(questions)

        # Recent activities logic
        scorecards_dir = "data/scorecards"
        activities = []
        if os.path.exists(scorecards_dir):
            for file in os.listdir(scorecards_dir):
                if file.endswith(".json"):
                    u_name = file[:-5]
                    card = load_json(os.path.join(scorecards_dir, file), {})
                    records = card.get("records", [])
                    for r in records:
                        activities.append({
                            "username": u_name,
                            "timestamp": r.get("timestamp", ""),
                            "question_text": r.get("question_text", ""),
                            "is_correct": r.get("is_correct", False),
                            "timed_out": r.get("timed_out", False)
                        })

        # Sort descending by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_activity_count = len(activities)

        # Build activity rows
        activity_rows = ""
        if activities:
            for act in activities[:5]:
                dt = datetime.datetime.fromisoformat(act["timestamp"]).strftime("%b %d, %Y %I:%M %p")
                
                badge = ""
                if act["timed_out"]:
                    badge = f'<span class="badge badge-error">{self.t["badge_timed_out"]}</span>'
                elif act["is_correct"]:
                    badge = f'<span class="badge badge-success">{self.t["badge_correct"]}</span>'
                else:
                    badge = f'<span class="badge badge-error">{self.t["badge_incorrect"]}</span>'

                activity_rows += f"""
                <tr>
                    <td style="font-weight: 600;">{act["username"]}</td>
                    <td>{act["question_text"]}</td>
                    <td>{dt}</td>
                    <td>{badge}</td>
                </tr>
                """
        else:
            activity_rows = f"<tr><td colspan='4' style='text-align: center; color: var(--text-muted);'>{self.t['no_activity']}</td></tr>"

        # Generate language options dynamically
        available_langs = get_available_languages()
        lang_options = ""
        for lang_opt in available_langs:
            selected_attr = "selected" if lang_opt["code"] == self.lang_code else ""
            lang_options += f'<option value="{lang_opt["code"]}" {selected_attr}>{lang_opt["name"]}</option>'

        # Generate questions file options dynamically
        available_files = get_available_questions_files()
        config = load_json("data/config.json", {})
        quiz_labels = config.get("quiz_labels", {})
        questions_file_options = ""
        for q_file in available_files:
            selected_attr = "selected" if q_file == active_q_file else ""
            label = quiz_labels.get(q_file, "")
            display_name = f"{q_file} ({label})" if label else q_file
            questions_file_options += f'<option value="{q_file}" {selected_attr}>{display_name}</option>'

        content = f"""
        <h2>{self.t['dashboard_title']}</h2>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-label">{self.t['metric_students']}</div>
                <div class="metric-value">{student_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">{self.t['metric_questions']}</div>
                <div class="metric-value">{question_count}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">{self.t['metric_submissions']}</div>
                <div class="metric-value">{recent_activity_count}</div>
            </div>
        </div>

        <div class="card">
            <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1rem;">{self.t['recent_activity']}</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width: 15%;">{self.t['table_student']}</th>
                        <th style="width: 50%;">{self.t['table_question']}</th>
                        <th style="width: 20%;">{self.t['table_datetime']}</th>
                        <th style="width: 15%;">{self.t['table_result']}</th>
                    </tr>
                </thead>
                <tbody>
                    {activity_rows}
                </tbody>
            </table>
        </div>

        <div class="card">
            <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1rem;">{self.t['global_settings']}</h3>
            <form action="/settings/save" method="POST">
                <div class="input-group" style="margin-bottom: 1.5rem;">
                    <label class="input-label" for="language">{self.t['global_language_label']}</label>
                    <select id="language" name="language" style="max-width: 300px;">
                        {lang_options}
                    </select>
                </div>
                <div class="input-group" style="margin-bottom: 1.5rem;">
                    <label class="input-label" for="questions_file">{self.t['active_questions_file_label']}</label>
                    <select id="questions_file" name="questions_file" style="max-width: 300px;">
                        {questions_file_options}
                    </select>
                </div>
                <button type="submit" class="btn">{self.t['btn_save_settings']}</button>
            </form>
        </div>
        """
        self.render_page("Dashboard", "dashboard", content, session)

    def show_students_list(self, session, success_msg, error_msg):
        users = load_json("data/users.json", [])
        students = [u for u in users if u.get("role") == "student"]

        alert_html = ""
        if success_msg:
            translated_msg = get_translated_message(success_msg, self.t)
            alert_html = f'<div class="alert alert-success">{translated_msg}</div>'
        elif error_msg:
            translated_err = get_translated_message(error_msg, self.t)
            alert_html = f'<div class="alert alert-error">{translated_err}</div>'

        student_rows = ""
        for s in students:
            username = s["username"]
            role = s.get("role", "student")
            
            # Load stats
            scorecard = load_json(f"data/scorecards/{username}.json", {})
            records = scorecard.get("records", [])
            
            total_answered = len(records)
            total_correct = sum(1 for r in records if r.get("is_correct", False))
            
            percentage = 0
            if total_answered > 0:
                percentage = int((total_correct / total_answered) * 100)
            
            percentage_color = "success" if percentage >= 60 else ("error" if percentage > 0 else "")

            # Translate role
            translated_role = self.t['option_student'] if role == "student" else (self.t['option_admin'] if role == "admin" else role)

            student_rows += f"""
            <tr>
                <td style="font-weight: 600;">{username}</td>
                <td>{translated_role}</td>
                <td>{total_answered}</td>
                <td>{total_correct}</td>
                <td class="score-stat-value {percentage_color}" style="font-size: 1.1rem; font-weight: 700;">{percentage}%</td>
                <td>
                    <div style="display: flex; gap: 0.5rem; justify-content: flex-end;">
                        <a href="/students/detail?username={username}" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">{self.t['btn_view_scorecard']}</a>
                        <a href="/students/reset-password?username={username}" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.35rem 0.75rem; color: var(--accent);">{self.t['btn_reset_password']}</a>
                        <form action="/students/delete" method="POST" onsubmit="return confirm('{self.t['delete_confirm']}');" style="margin:0;">
                            <input type="hidden" name="username" value="{username}">
                            <button type="submit" class="btn btn-danger" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">{self.t['btn_delete']}</button>
                        </form>
                    </div>
                </td>
            </tr>
            """

        if not students:
            student_rows = f"<tr><td colspan='6' style='text-align: center; color: var(--text-muted);'>{self.t['no_students']}</td></tr>"

        content = f"""
        <h2>{self.t['students_title']}</h2>
        {alert_html}
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th style="width: 20%;">{self.t['table_username']}</th>
                        <th style="width: 12%;">{self.t['table_role']}</th>
                        <th style="width: 15%;">{self.t['table_total_answered']}</th>
                        <th style="width: 13%;">{self.t['table_total_correct']}</th>
                        <th style="width: 15%;">{self.t['table_avg_score']}</th>
                        <th style="width: 25%; text-align: right;">{self.t['table_actions']}</th>
                    </tr>
                </thead>
                <tbody>
                    {student_rows}
                </tbody>
            </table>
        </div>
        """
        self.render_page("Students List", "students", content, session)

    def show_add_student(self, session):
        content = f"""
        <h2>{self.t['create_user_title']}</h2>
        <div class="card" style="max-width: 500px; margin: 0 auto;">
            <form action="/students/add" method="POST">
                <div class="input-group">
                    <label class="input-label" for="username">{self.t['label_username']}</label>
                    <input type="text" id="username" name="username" required autocomplete="off">
                </div>
                <div class="input-group">
                    <label class="input-label" for="password">{self.t['label_password']}</label>
                    <input type="password" id="password" name="password" required autocomplete="off">
                </div>
                <div class="input-group" style="margin-bottom: 2rem;">
                    <label class="input-label" for="role">{self.t['label_role']}</label>
                    <select id="role" name="role">
                        <option value="student">{self.t['option_student']}</option>
                        <option value="admin">{self.t['option_admin']}</option>
                    </select>
                </div>
                <button type="submit" class="btn">{self.t['btn_create_user']}</button>
            </form>
        </div>
        """
        self.render_page("Add Student", "add", content, session)

    def show_reset_password(self, session, username):
        info_text = self.t['reset_password_info'].format(username=username)
        content = f"""
        <h2>{self.t['reset_password_title']}</h2>
        <div class="card" style="max-width: 500px; margin: 0 auto;">
            <p style="margin-bottom: 1.5rem; color: var(--text-muted);">{info_text}</p>
            <form action="/students/reset-password" method="POST">
                <input type="hidden" name="username" value="{username}">
                <div class="input-group" style="margin-bottom: 2rem;">
                    <label class="input-label" for="new_password">{self.t['label_new_password']}</label>
                    <input type="password" id="new_password" name="new_password" required autocomplete="off" autofocus>
                </div>
                <button type="submit" class="btn">{self.t['btn_update_password']}</button>
                <a href="/students" class="btn btn-secondary" style="display: block; text-align: center; margin-top: 1rem;">{self.t['btn_cancel']}</a>
            </form>
        </div>
        """
        self.render_page("Reset Password", "students", content, session)

    def show_student_detail(self, session, username):
        scorecard = load_json(f"data/scorecards/{username}.json", {})
        records = scorecard.get("records", [])

        records_rows = ""
        for i, r in enumerate(records):
            dt = datetime.datetime.fromisoformat(r["timestamp"]).strftime("%b %d, %Y %I:%M %p")
            
            badge = ""
            if r["timed_out"]:
                badge = f'<span class="badge badge-error">{self.t["badge_timed_out"]}</span>'
            elif r["is_correct"]:
                badge = f'<span class="badge badge-success">{self.t["badge_correct"]}</span>'
            else:
                badge = f'<span class="badge badge-error">{self.t["badge_incorrect"]}</span>'

            # Display student vs correct answer
            if r["timed_out"]:
                answers_disp = self.t["scorecard_timeout_format"].format(correct_answer=r["correct_answer"])
            else:
                answers_disp = self.t["scorecard_answer_format"].format(student_answer=r["student_answer"], correct_answer=r["correct_answer"])

            records_rows += f"""
            <tr>
                <td>{i+1}</td>
                <td style="font-weight: 500;">{r["question_text"]}</td>
                <td>{answers_disp}</td>
                <td>{badge}</td>
                <td>{dt}</td>
            </tr>
            """

        if not records:
            records_rows = f"<tr><td colspan='5' style='text-align: center; color: var(--text-muted);'>{self.t['no_records']}</td></tr>"

        title_text = self.t['scorecard_title'].format(username=username)
        content = f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem;">
            <h2>{title_text}</h2>
            <a href="/students" class="btn btn-secondary">&larr; {self.t['btn_back_students']}</a>
        </div>
        
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th style="width: 5%;">{self.t['table_num']}</th>
                        <th style="width: 45%;">{self.t['table_question_text']}</th>
                        <th style="width: 20%;">{self.t['table_answers']}</th>
                        <th style="width: 12%;">{self.t['table_result']}</th>
                        <th style="width: 18%;">{self.t['table_timestamp']}</th>
                    </tr>
                </thead>
                <tbody>
                    {records_rows}
                </tbody>
            </table>
        </div>
        """
        self.render_page(f"Scorecard: {username}", "students", content, session)

# =====================================================================
# SERVER RUNNER
# =====================================================================

def run_server(port=8081):
    """
    Main runner to start the admin-facing HTTP Server.
    """
    server_address = ("", port)
    httpd = HTTPServer(server_address, AdminAppHandler)
    print(f"Admin app started on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
