import os
import sys
import random
import time
import datetime
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer
from utils import BaseHandler, SessionStore, load_json, save_json, hash_password, generate_session_id, get_translations, get_translated_message, get_active_questions_file

# Initialize in-memory session store
quiz_sessions = SessionStore(expiry_seconds=1800)

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
  margin-bottom: 1rem;
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
  max-width: 800px;
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

.btn {
  display: inline-block;
  background-color: var(--accent);
  color: #000;
  font-weight: 700;
  font-family: inherit;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  text-align: center;
  width: 100%;
}

.btn:hover {
  background-color: var(--accent-hover);
  transform: translateY(-1px);
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

.progress-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.progress-bar {
  background: var(--border);
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 1.5rem;
}

.progress-fill {
  background: var(--accent);
  height: 100%;
  transition: width 0.3s ease;
}

.timer-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 1.5rem;
}

.timer {
  font-size: 2rem;
  font-weight: 700;
  color: var(--accent);
  background: var(--surface);
  border: 2px solid var(--border);
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.1);
}

.timer.warning {
  color: var(--error);
  border-color: var(--error);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.3);
  animation: pulse 1s infinite alternate;
}

@keyframes pulse {
  from { transform: scale(1); }
  to { transform: scale(1.05); }
}

.choices-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.choice-label {
  display: flex;
  align-items: center;
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 1rem;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.choice-label:hover {
  border-color: var(--accent);
  background: var(--surface-hover);
}

.choice-label input[type="radio"] {
  margin-right: 1rem;
  accent-color: var(--accent);
  width: 1.2rem;
  height: 1.2rem;
  cursor: pointer;
}

.choice-label.selected {
  border-color: var(--accent);
  background: rgba(245, 158, 11, 0.05);
}

.score-summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.score-stat {
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 1.5rem;
  border-radius: 8px;
  text-align: center;
}

.score-stat-label {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

.score-stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--accent);
}

.score-stat-value.success { color: var(--success); }
.score-stat-value.error { color: var(--error); }

.review-item {
  border-bottom: 1px solid var(--border);
  padding: 1.5rem 0;
}

.review-item:last-child {
  border-bottom: none;
}

.review-question {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.review-choices {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.review-choice {
  padding: 0.75rem 1rem;
  border-radius: 4px;
  font-size: 0.85rem;
  border: 1px solid var(--border);
  background: var(--bg);
}

.review-choice.correct {
  background: rgba(34, 197, 94, 0.1);
  border-color: var(--success);
  color: var(--success);
}

.review-choice.student-wrong {
  background: rgba(239, 68, 68, 0.1);
  border-color: var(--error);
  color: var(--error);
}

.review-choice.muted {
  color: var(--text-muted);
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

class QuizAppHandler(BaseHandler):
    """
    HTTP request handler for the student quiz site. Handles student authentication,
    quiz generation, timer progression, and score tracking.
    """

    def do_GET(self):
        # Load translations once per request
        self.lang_code, self.t = get_translations()

        url = urlparse(self.path)
        path = url.path

        # 1. Login Endpoint
        if path == "/login":
            error_msg = parse_qs(url.query).get("error", [None])[0]
            self.show_login(error_msg)
            return

        # 2. Check Auth
        session = self.get_session(quiz_sessions)
        if not session:
            self.redirect("/login")
            return

        # 3. Logout Endpoint
        if path == "/logout":
            quiz_sessions.delete(session["session_id"])
            self.set_cookie("session_id", "", max_age=-1)
            self.redirect("/login")
            return

        # 4. Retake Endpoint
        if path == "/retake":
            config = load_json("data/config.json", {})
            allow_retake = config.get("allow_retake", True)
            if allow_retake:
                # Clear student quiz session data
                if "question_list" in session:
                    del session["question_list"]
                if "current_question_index" in session:
                    del session["current_question_index"]
                if "quiz_session_id" in session:
                    del session["quiz_session_id"]
                if "start_time_of_current_question" in session:
                    del session["start_time_of_current_question"]
            self.redirect("/")
            return

        # 5. Main Quiz / Dashboard Entrypoint
        if path == "/":
            self.show_quiz(session)
            return

        # 404 Fallback
        self.send_html("<h1>404 Not Found</h1>", status=404)

    def do_POST(self):
        # Load translations once per request
        self.lang_code, self.t = get_translations()

        url = urlparse(self.path)
        path = url.path

        # 1. Authentication Submission
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
                # We also block admins from taking the student quiz
                if user.get("role") != "student":
                    self.redirect("/login?error=err_student_login_admin")
                    return
                
                session = quiz_sessions.create(username)
                self.set_cookie("session_id", session["session_id"])
                self.redirect("/")
            else:
                self.redirect("/login?error=err_invalid_credentials")
            return

        # Check Auth for POST requests
        session = self.get_session(quiz_sessions)
        if not session:
            self.redirect("/login")
            return

        # 2. Answer Submission
        if path == "/submit":
            if "question_list" not in session or "current_question_index" not in session:
                self.redirect("/")
                return

            idx = session["current_question_index"]
            questions = session["question_list"]
            if idx >= len(questions):
                self.redirect("/")
                return

            question = questions[idx]
            config = load_json("data/config.json", {})

            post_data = self.parse_post_body()
            student_answer = post_data.get("answer")

            # Validate time elapsed on the backend to prevent cheating
            limit = question.get("timeout_override") or config.get("timeout_seconds", 30)
            elapsed = time.time() - session.get("start_time_of_current_question", time.time())

            timed_out = False
            # Allow a 3-second network latency grace period
            if (limit > 0 and elapsed > limit + 3.0) or student_answer == "TIMEOUT":
                timed_out = True
                student_answer = "TIMEOUT"

            username = session["username"]
            scorecard = load_json(f"data/scorecards/{username}.json", {"username": username, "records": []})

            is_correct = (student_answer == question["correct"]) and not timed_out

            record = {
                "session_id": session.get("quiz_session_id"),
                "timestamp": datetime.datetime.now().isoformat(),
                "question_id": question["id"],
                "question_text": question["question"],
                "choices_presented": question["choices"],
                "student_answer": student_answer if student_answer else "NO ANSWER",
                "correct_answer": question["correct"],
                "is_correct": is_correct,
                "timed_out": timed_out
            }
            scorecard["records"].append(record)
            save_json(f"data/scorecards/{username}.json", scorecard)

            # Advance to next question
            session["current_question_index"] += 1
            session["start_time_of_current_question"] = time.time()

            self.redirect("/")
            return

        self.send_html("<h1>404 Not Found</h1>", status=404)

    # =====================================================================
    # HTML RENDERING HELPERS
    # =====================================================================

    def show_login(self, error_msg):
        translated_err = get_translated_message(error_msg, self.t)
        error_html = f'<div class="alert alert-error">{translated_err}</div>' if error_msg else ''
        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{self.t['student_login_title']}</title>
    <style>{COMMON_CSS}</style>
</head>
<body>
    <header>
        <div class="header-title">{self.t['student_login_header']}</div>
    </header>
    <div class="container" style="max-width: 450px; margin-top: 6rem;">
        <div class="card">
            <h2 style="text-align: center; margin-bottom: 1.5rem; color: var(--accent);">{self.t['student_login_card']}</h2>
            {error_html}
            <form action="/login" method="POST">
                <div class="input-group">
                    <label class="input-label" for="username">{self.t['student_username_label']}</label>
                    <input type="text" id="username" name="username" required autocomplete="username" autofocus>
                </div>
                <div class="input-group" style="margin-bottom: 2rem;">
                    <label class="input-label" for="password">{self.t['student_password_label']}</label>
                    <input type="password" id="password" name="password" required autocomplete="current-password">
                </div>
                <button type="submit" class="btn">{self.t['student_sign_in']}</button>
            </form>
        </div>
    </div>
    <footer>
        &copy; {datetime.datetime.now().year} {self.t['footer_text']}
    </footer>
</body>
</html>"""
        self.send_html(html)

    def show_quiz(self, session):
        username = session["username"]
        config = load_json("data/config.json", {
            "quiz_title": "Photography Knowledge Quiz",
            "timeout_seconds": 30,
            "questions_per_session": 5,
            "allow_retake": True
        })
        allow_retake = config.get("allow_retake", True)

        # Load scorecard history
        scorecard = load_json(f"data/scorecards/{username}.json", {"username": username, "records": []})
        has_completed_before = len(scorecard.get("records", [])) > 0

        # Create session questions list if not initialized
        if "question_list" not in session:
            if not allow_retake and has_completed_before:
                # Retakes not allowed, render the last summary immediately
                self.show_summary(username, scorecard, None)
                return

            q_file = get_active_questions_file()
            all_questions = load_json(os.path.join("data", q_file), [])
            if not all_questions:
                self.send_html(f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head><style>""" + COMMON_CSS + """</style></head>
<body>
<header><div class="header-title">{config.get("quiz_title", "Photography Quiz")}</div></header>
<div class="container"><div class="card"><h2>Error</h2><p>{self.t['no_questions_err']}</p></div></div>
</body>
</html>""")
                return

            n = min(config.get("questions_per_session", 5), len(all_questions))
            selected = random.sample(all_questions, n)

            session["question_list"] = selected
            session["current_question_index"] = 0
            session["quiz_session_id"] = generate_session_id()
            session["start_time_of_current_question"] = time.time()

        idx = session["current_question_index"]
        questions = session["question_list"]

        if idx < len(questions):
            question = questions[idx]
            
            # Check for backend timeout during GET request
            limit = question.get("timeout_override") or config.get("timeout_seconds", 30)
            elapsed = time.time() - session.get("start_time_of_current_question", time.time())
            
            if limit > 0 and elapsed > limit:
                # Automatically process timeout and reload
                self.process_timeout(session, question)
                self.redirect("/")
                return

            self.show_question_page(session, idx, len(questions), question, config)
        else:
            self.show_summary(username, scorecard, session.get("quiz_session_id"))

    def process_timeout(self, session, question):
        """
        Helper method to register a timeout record and step the quiz.
        """
        username = session["username"]
        scorecard = load_json(f"data/scorecards/{username}.json", {"username": username, "records": []})
        
        record = {
            "session_id": session.get("quiz_session_id"),
            "timestamp": datetime.datetime.now().isoformat(),
            "question_id": question["id"],
            "question_text": question["question"],
            "choices_presented": question["choices"],
            "student_answer": "TIMEOUT",
            "correct_answer": question["correct"],
            "is_correct": False,
            "timed_out": True
        }
        scorecard["records"].append(record)
        save_json(f"data/scorecards/{username}.json", scorecard)

        session["current_question_index"] += 1
        session["start_time_of_current_question"] = time.time()

    def show_question_page(self, session, index, total, question, config):
        username = session["username"]
        active_file = get_active_questions_file()
        quiz_labels = config.get("quiz_labels", {})
        quiz_title = quiz_labels.get(active_file) or config.get("quiz_title") or "Photography Quiz"
        limit = question.get("timeout_override") or config.get("timeout_seconds", 30)
        elapsed = time.time() - session.get("start_time_of_current_question", time.time())
        time_left = max(0, int(limit - elapsed)) if limit > 0 else 0

        # Calculate progress percentage
        progress_percentage = int(((index) / total) * 100)
        
        # Build choices inputs
        choices_html = ""
        for letter in sorted(question["choices"].keys()):
            text = question["choices"][letter]
            choices_html += f"""
            <label class="choice-label" id="label-{letter}">
                <input type="radio" name="answer" value="{letter}" required onclick="selectChoice('{letter}')">
                <span><strong>{letter}:</strong> {text}</span>
            </label>
            """

        timer_section = ""
        timer_script = ""
        if limit > 0:
            timer_section = f"""
            <div class="timer-container">
                <div class="timer" id="timer">{time_left}s</div>
            </div>
            """
            timer_script = f"""
            let timeLeft = {time_left};
            const timerEl = document.getElementById('timer');
            const formEl = document.getElementById('quiz-form');
            
            const countdown = setInterval(() => {{
                timeLeft--;
                if (timerEl) {{
                    timerEl.textContent = timeLeft + 's';
                    if (timeLeft < 10) {{
                        timerEl.classList.add('warning');
                    }}
                }}
                if (timeLeft <= 0) {{
                    clearInterval(countdown);
                    // Force submit as timeout
                    document.querySelectorAll('input[type="radio"]').forEach(r => r.disabled = true);
                    const timeoutInput = document.createElement('input');
                    timeoutInput.type = 'hidden';
                    timeoutInput.name = 'answer';
                    timeoutInput.value = 'TIMEOUT';
                    formEl.appendChild(timeoutInput);
                    formEl.submit();
                }}
            }}, 1000);
            """

        student_badge_text = self.t['student_badge'].format(username=username)
        progress_text = self.t['question_progress'].format(current=index + 1, total=total)
        percentage_text = self.t['complete_percentage'].format(percentage=progress_percentage)

        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{quiz_title}</title>
    <style>{COMMON_CSS}</style>
    <script>
        function selectChoice(letter) {{
            // Remove selection class from all labels
            document.querySelectorAll('.choice-label').forEach(label => {{
                label.classList.remove('selected');
            }});
            // Add to selected label
            const activeLabel = document.getElementById('label-' + letter);
            if (activeLabel) {{
                activeLabel.classList.add('selected');
            }}
        }}
    </script>
</head>
<body>
    <header>
        <div class="header-title">{quiz_title}</div>
        <div class="header-right">
            <span class="user-badge">{student_badge_text}</span>
            <a href="/logout" class="logout-link">{self.t['logout']}</a>
        </div>
    </header>
    <div class="container">
        {timer_section}
        
        <div class="progress-container">
            <span>{progress_text}</span>
            <span>{percentage_text}</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress_percentage}%;"></div>
        </div>

        <div class="card">
            <form id="quiz-form" action="/submit" method="POST">
                <h2 style="font-size: 1.25rem; line-height: 1.6; margin-bottom: 2rem;">{question["question"]}</h2>
                
                <div class="choices-list">
                    {choices_html}
                </div>
                
                <button type="submit" class="btn" style="margin-top: 1rem;">{self.t['submit_continue']}</button>
            </form>
        </div>
    </div>
    <footer>
        &copy; {datetime.datetime.now().year} {self.t['footer_text']}
    </footer>
    <script>
        {timer_script}
    </script>
</body>
</html>"""
        self.send_html(html)

    def show_summary(self, username, scorecard, quiz_session_id):
        records = scorecard.get("records", [])
        if not records:
            self.show_no_records_page(username)
            return

        # If no quiz_session_id is active, find the latest session in scorecard
        if not quiz_session_id:
            quiz_session_id = records[-1]["session_id"]

        session_records = [r for r in records if r["session_id"] == quiz_session_id]
        if not session_records:
            # Fallback
            quiz_session_id = records[-1]["session_id"]
            session_records = [r for r in records if r["session_id"] == quiz_session_id]

        correct_count = sum(1 for r in session_records if r["is_correct"])
        total_count = len(session_records)
        percentage = int((correct_count / total_count) * 100) if total_count > 0 else 0

        config = load_json("data/config.json", {})
        active_file = get_active_questions_file()
        quiz_labels = config.get("quiz_labels", {})
        quiz_title = quiz_labels.get(active_file) or config.get("quiz_title") or "Photography Quiz"
        allow_retake = config.get("allow_retake", True)

        # Build Q&A review items
        review_html = ""
        for i, r in enumerate(session_records):
            status_badge = ""
            if r["timed_out"]:
                status_badge = f'<span class="badge badge-error">{self.t["badge_timed_out"]}</span>'
            elif r["is_correct"]:
                status_badge = f'<span class="badge badge-success">{self.t["badge_correct"]}</span>'
            else:
                status_badge = f'<span class="badge badge-error">{self.t["badge_incorrect"]}</span>'

            choices_block = ""
            for letter in sorted(r["choices_presented"].keys()):
                choice_text = r["choices_presented"][letter]
                item_class = "review-choice"
                
                # Check formatting
                if letter == r["correct_answer"]:
                    item_class += " correct"
                elif letter == r["student_answer"] and not r["is_correct"]:
                    item_class += " student-wrong"
                else:
                    item_class += " muted"
                    
                student_indicator = f" &nbsp;&nbsp;&larr; {self.t['your_answer']}" if letter == r["student_answer"] else ""
                correct_indicator = f" ({self.t['correct_answer_indicator']})" if letter == r["correct_answer"] else ""
                
                choices_block += f"""
                <div class="{item_class}">
                    <strong>{letter}:</strong> {choice_text}{student_indicator}{correct_indicator}
                </div>
                """

            review_html += f"""
            <div class="review-item">
                <div class="review-question">
                    <span><strong>Q{i+1}:</strong> {r["question_text"]}</span>
                    {status_badge}
                </div>
                <div class="review-choices">
                    {choices_block}
                </div>
            </div>
            """

        retake_btn = ""
        if allow_retake:
            retake_btn = f'<a href="/retake" class="btn" style="text-align: center; margin-top: 1rem;">{self.t["take_again"]}</a>'
        else:
            retake_btn = f'<div class="alert alert-warning" style="text-align: center;">{self.t["retakes_disabled"]}</div>'

        student_badge_text = self.t['student_badge'].format(username=username)

        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{self.t['quiz_summary_title']} - {quiz_title}</title>
    <style>{COMMON_CSS}</style>
</head>
<body>
    <header>
        <div class="header-title">{quiz_title}</div>
        <div class="header-right">
            <span class="user-badge">{student_badge_text}</span>
            <a href="/logout" class="logout-link">{self.t['logout']}</a>
        </div>
    </header>
    <div class="container">
        <h2 style="text-align: center; margin-bottom: 2rem;">{self.t['quiz_completed']}</h2>
        
        <div class="score-summary-grid">
            <div class="score-stat">
                <div class="score-stat-label">{self.t['final_score']}</div>
                <div class="score-stat-value { 'success' if percentage >= 60 else 'error' }">{correct_count} / {total_count}</div>
            </div>
            <div class="score-stat">
                <div class="score-stat-label">{self.t['percentage']}</div>
                <div class="score-stat-value { 'success' if percentage >= 60 else 'error' }">{percentage}%</div>
            </div>
        </div>

        <div class="card">
            <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 1rem; margin-bottom: 1.5rem;">{self.t['question_review']}</h3>
            {review_html}
        </div>

        <div style="max-width: 300px; margin: 2rem auto 0 auto;">
            {retake_btn}
        </div>
    </div>
    <footer>
        &copy; {datetime.datetime.now().year} {self.t['footer_text']}
    </footer>
</body>
</html>"""
        self.send_html(html)

    def show_no_records_page(self, username):
        config = load_json("data/config.json", {})
        active_file = get_active_questions_file()
        quiz_labels = config.get("quiz_labels", {})
        quiz_title = quiz_labels.get(active_file) or config.get("quiz_title") or "Photography Quiz"
        
        student_badge_text = self.t['student_badge'].format(username=username)
        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{self.t['quiz_summary_title']} - {quiz_title}</title>
    <style>{COMMON_CSS}</style>
</head>
<body>
    <header>
        <div class="header-title">{quiz_title}</div>
        <div class="header-right">
            <span class="user-badge">{student_badge_text}</span>
            <a href="/logout" class="logout-link">{self.t['logout']}</a>
        </div>
    </header>
    <div class="container">
        <div class="card" style="text-align: center; padding: 3rem;">
            <h2>{self.t['no_records_title']}</h2>
            <p style="color: var(--text-muted); margin-bottom: 2rem;">{self.t['no_records_desc']}</p>
            <a href="/" class="btn" style="max-width: 200px; margin: 0 auto; display: block;">{self.t['start_quiz']}</a>
        </div>
    </div>
    <footer>
        &copy; {datetime.datetime.now().year} {self.t['footer_text']}
    </footer>
</body>
</html>"""
        self.send_html(html)

# =====================================================================
# SERVER RUNNER
# =====================================================================

def run_server(port=8080):
    """
    Main runner to start the student-facing HTTP Server.
    """
    server_address = ("", port)
    httpd = HTTPServer(server_address, QuizAppHandler)
    print(f"Student quiz app started on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
