import os
import sys
import datetime
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer
from utils import BaseHandler, load_json, save_json, get_translations, get_translated_message, get_active_questions_file, get_available_questions_files

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
  max-width: 1100px;
  margin: 2rem auto;
  padding: 0 1rem;
  width: 100%;
  flex: 1;
}

.editor-layout {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 2rem;
  align-items: start;
}

@media (max-width: 768px) {
  .editor-layout {
    grid-template-columns: 1fr;
  }
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

.question-item {
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 1.25rem;
  margin-bottom: 1rem;
  background: var(--bg);
}

.question-meta {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-bottom: 0.75rem;
}

.question-text {
  font-size: 0.95rem;
  font-weight: 500;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.question-actions {
  display: flex;
  gap: 0.5rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}

.badge-info {
  background: rgba(245, 158, 11, 0.15);
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

def generate_new_question_id(questions):
    """
    Scans the existing list of questions and returns the next incremented ID.
    Supports standard 'q001', 'q002' format.
    """
    if not questions:
        return "q001"
    max_id = 0
    for q in questions:
        q_id = q.get("id", "")
        if q_id.startswith("q") and q_id[1:].isdigit():
            try:
                num = int(q_id[1:])
                if num > max_id:
                    max_id = num
            except ValueError:
                pass
    return f"q{max_id + 1:03d}"

class EditorAppHandler(BaseHandler):
    """
    HTTP Request Handler for Port 8083 (Question Editor).
    No login required, manages questions database file.
    """

    def do_GET(self):
        # Load translations once per request
        self.lang_code, self.t = get_translations()

        url = urlparse(self.path)
        path = url.path
        params = parse_qs(url.query)

        # 1. Determine which file is being edited
        editing_file = params.get("file", [None])[0]
        if not editing_file:
            editing_file = get_active_questions_file()

        # 2. Action Routing
        if path == "/":
            action = params.get("action", [None])[0]
            question_id = params.get("id", [None])[0]
            
            # Handle Delete action inline on GET (to keep design simple)
            if action == "delete" and question_id:
                editing_filepath = os.path.join("data", editing_file)
                questions = load_json(editing_filepath, [])
                filtered = [q for q in questions if q["id"] != question_id]
                if len(filtered) < len(questions):
                    save_json(editing_filepath, filtered)
                    self.redirect(f"/?file={editing_file}&msg=msg_question_deleted")
                else:
                    self.redirect(f"/?file={editing_file}&err=err_question_not_found")
                return

            # Main dashboard view
            self.show_editor(action, question_id, params, editing_file)
            return

        # 404 Fallback
        self.send_html("<h1>404 Not Found</h1>", status=404)

    def do_POST(self):
        # Load translations once per request
        self.lang_code, self.t = get_translations()

        url = urlparse(self.path)
        path = url.path

        # 1. Handle question Save/Update
        if path == "/save":
            post_data = self.parse_post_body()
            question_id = post_data.get("id", "").strip() # Hidden field when editing
            question_text = post_data.get("question", "").strip()
            choice_A = post_data.get("choice_A", "").strip()
            choice_B = post_data.get("choice_B", "").strip()
            choice_C = post_data.get("choice_C", "").strip()
            choice_D = post_data.get("choice_D", "").strip()
            correct = post_data.get("correct", "").strip()
            timeout_override_str = post_data.get("timeout_override", "").strip()
            editing_file = post_data.get("file", "").strip()
            if not editing_file:
                editing_file = get_active_questions_file()

            # Input validation
            if not question_text or not choice_A or not choice_B or not choice_C or not choice_D or not correct:
                back_to = f"/?file={editing_file}&action=edit&id={question_id}&err=err_fields_required" if question_id else f"/?file={editing_file}&err=err_fields_required"
                self.redirect(back_to)
                return

            # Parse timeout override
            timeout_override = None
            if timeout_override_str and timeout_override_str != "0":
                try:
                    timeout_override = int(timeout_override_str)
                except ValueError:
                    timeout_override = None

            editing_filepath = os.path.join("data", editing_file)
            questions = load_json(editing_filepath, [])

            if question_id:
                # Update existing question
                updated = False
                for q in questions:
                    if q["id"] == question_id:
                        q["question"] = question_text
                        q["choices"] = {
                            "A": choice_A,
                            "B": choice_B,
                            "C": choice_C,
                            "D": choice_D
                        }
                        q["correct"] = correct
                        q["timeout_override"] = timeout_override
                        updated = True
                        break
                if updated:
                    save_json(editing_filepath, questions)
                    self.redirect(f"/?file={editing_file}&msg=msg_question_updated")
                else:
                    self.redirect(f"/?file={editing_file}&err=err_question_not_found_id:{question_id}")
            else:
                # Insert new question
                new_id = generate_new_question_id(questions)
                new_question = {
                    "id": new_id,
                    "question": question_text,
                    "choices": {
                        "A": choice_A,
                        "B": choice_B,
                        "C": choice_C,
                        "D": choice_D
                    },
                    "correct": correct,
                    "timeout_override": timeout_override
                }
                questions.append(new_question)
                save_json(editing_filepath, questions)
                self.redirect(f"/?file={editing_file}&msg=msg_question_added")
            return

        # 2. Handle create new file
        if path == "/create_file":
            post_data = self.parse_post_body()
            filename_suffix = post_data.get("filename", "").strip()
            
            import re
            if not filename_suffix or not re.match(r"^[a-zA-Z0-9_]+$", filename_suffix):
                self.redirect("/?err=err_invalid_filename")
                return
                
            if not filename_suffix.startswith("question_"):
                new_filename = f"question_{filename_suffix}.json"
            else:
                new_filename = f"{filename_suffix}.json"
                
            new_filepath = os.path.join("data", new_filename)
            if not os.path.exists(new_filepath):
                save_json(new_filepath, [])
                
            self.redirect(f"/?file={new_filename}&msg=msg_file_created")
            return

        # 3. Handle save quiz label
        if path == "/save_quiz_label":
            post_data = self.parse_post_body()
            editing_file = post_data.get("file", "").strip()
            quiz_label = post_data.get("quiz_label", "").strip()
            
            if not editing_file:
                editing_file = get_active_questions_file()
                
            if quiz_label:
                config = load_json("data/config.json", {})
                if "quiz_labels" not in config:
                    config["quiz_labels"] = {}
                config["quiz_labels"][editing_file] = quiz_label
                save_json("data/config.json", config)
                self.redirect(f"/?file={editing_file}&msg=msg_settings_updated")
            else:
                self.redirect(f"/?file={editing_file}&err=err_fields_required")
            return

        self.send_html("<h1>404 Not Found</h1>", status=404)

    # =====================================================================
    # HTML RENDERING HELPERS
    # =====================================================================

    def show_editor(self, action, question_id, params, editing_file):
        editing_filepath = os.path.join("data", editing_file)
        questions = load_json(editing_filepath, [])
        
        # Parse query notices/flashes
        success_msg = params.get("msg", [None])[0]
        error_msg = params.get("err", [None])[0]

        alert_html = ""
        if success_msg:
            translated_msg = get_translated_message(success_msg, self.t)
            alert_html = f'<div class="alert alert-success">{translated_msg}</div>'
        elif error_msg:
            translated_err = get_translated_message(error_msg, self.t)
            alert_html = f'<div class="alert alert-error">{translated_err}</div>'

        # Locate question for editing if action == edit
        edit_q = None
        if action == "edit" and question_id:
            for q in questions:
                if q["id"] == question_id:
                    edit_q = q
                    break

        # Render questions list panel
        questions_list_html = ""
        for q in questions:
            truncated_text = q["question"]
            if len(truncated_text) > 85:
                truncated_text = truncated_text[:85] + "..."
            
            timeout_badge = ""
            if q.get("timeout_override") is not None:
                timeout_badge = f'<span class="badge badge-info" style="margin-left: 0.5rem;">Timeout: {q["timeout_override"]}s</span>'

            delete_confirm_str = self.t['delete_question_confirm'].format(id=q["id"])

            questions_list_html += f"""
            <div class="question-item">
                <div class="question-meta">
                    <span><strong>ID: {q["id"]}</strong></span>
                    <div>
                        <span class="badge badge-success" style="background: rgba(34, 197, 94, 0.15);">{self.t['badge_correct']}: {q["correct"]}</span>
                        {timeout_badge}
                    </div>
                </div>
                <div class="question-text">{truncated_text}</div>
                <div class="question-actions">
                    <a href="/?file={editing_file}&action=edit&id={q["id"]}" class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;">{self.t['btn_edit']}</a>
                    <a href="/?file={editing_file}&action=delete&id={q["id"]}" class="btn btn-danger" style="font-size: 0.8rem; padding: 0.35rem 0.75rem;" onclick="return confirm('{delete_confirm_str}');">{self.t['btn_delete']}</a>
                </div>
            </div>
            """

        if not questions:
            questions_list_html = f'<p style="text-align: center; color: var(--text-muted); padding: 3rem 0;">{self.t["no_questions"]}</p>'

        # Configure edit or add form details
        form_title = self.t['add_question_title']
        hidden_id_input = ""
        form_q_text = ""
        form_choice_A = ""
        form_choice_B = ""
        form_choice_C = ""
        form_choice_D = ""
        form_correct_options = { "A": "", "B": "", "C": "", "D": "" }
        form_timeout_override = ""
        cancel_btn = ""

        if edit_q:
            form_title = self.t['edit_question_title'].format(id=edit_q['id'])
            hidden_id_input = f'<input type="hidden" name="id" value="{edit_q["id"]}">'
            form_q_text = edit_q["question"]
            form_choice_A = edit_q["choices"].get("A", "")
            form_choice_B = edit_q["choices"].get("B", "")
            form_choice_C = edit_q["choices"].get("C", "")
            form_choice_D = edit_q["choices"].get("D", "")
            form_correct_options[edit_q["correct"]] = "selected"
            if edit_q.get("timeout_override") is not None:
                form_timeout_override = str(edit_q["timeout_override"])
            cancel_btn = f'<a href="/?file={editing_file}" class="btn btn-secondary" style="display: block; text-align: center; margin-top: 1rem;">{self.t["btn_cancel_edit"]}</a>'

        db_title = self.t['question_db_title'].format(count=len(questions))

        # Generate questions file options dynamically for editing
        available_files = get_available_questions_files()
        config = load_json("data/config.json", {})
        quiz_labels = config.get("quiz_labels", {})
        current_quiz_label = quiz_labels.get(editing_file, "")
        if not current_quiz_label:
            if config.get("questions_file") == editing_file:
                current_quiz_label = config.get("quiz_title", "")
            else:
                current_quiz_label = editing_file.replace(".json", "").replace("_", " ").title()

        questions_file_options = ""
        for q_file in available_files:
            selected_attr = "selected" if q_file == editing_file else ""
            label = quiz_labels.get(q_file, "")
            display_name = f"{q_file} ({label})" if label else q_file
            questions_file_options += f'<option value="{q_file}" {selected_attr}>{display_name}</option>'

        html = f"""<!DOCTYPE html>
<html lang="{self.lang_code}">
<head>
    <meta charset="UTF-8">
    <title>{self.t['editor_title']}</title>
    <style>{COMMON_CSS}</style>
</head>
<body>
    <header>
        <div class="header-title">{self.t['editor_header']}</div>
        <div style="display: flex; align-items: center; gap: 1.5rem;">
            <!-- Select file to edit -->
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <label style="font-size: 0.85rem; color: var(--text-muted);">{self.t['editor_select_file_label']}:</label>
                <select onchange="window.location.href='/?file=' + this.value" style="padding: 0.35rem; border-radius: 4px; background: var(--surface); color: var(--text); border: 1px solid var(--border); width: auto;">
                    {questions_file_options}
                </select>
            </div>
            <!-- Create new questions file -->
            <form action="/create_file" method="POST" style="display: flex; align-items: center; gap: 0.5rem; margin: 0;">
                <input type="text" name="filename" placeholder="{self.t['placeholder_new_file']}" required style="padding: 0.35rem; border-radius: 4px; background: var(--bg); color: var(--text); border: 1px solid var(--border); max-width: 150px;">
                <button type="submit" class="btn" style="font-size: 0.85rem; padding: 0.35rem 0.75rem;">{self.t['btn_create_new_file']}</button>
            </form>
            <a href="/?file={editing_file}" class="btn btn-secondary" style="font-size: 0.85rem; padding: 0.35rem 0.75rem;">{self.t['btn_refresh']}</a>
        </div>
    </header>
    
    <div class="container">
        {alert_html}
        
        <!-- Quiz Label Editor Card -->
        <div class="card" style="margin-bottom: 1.5rem; padding: 1.5rem;">
            <form action="/save_quiz_label" method="POST" style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                <input type="hidden" name="file" value="{editing_file}">
                <label style="font-weight: 600; font-size: 0.9rem; white-space: nowrap; color: var(--accent);">Quiz Title / Label:</label>
                <input type="text" name="quiz_label" value="{current_quiz_label}" placeholder="Enter quiz title..." required style="flex: 1; min-width: 200px; padding: 0.5rem; background-color: var(--bg); border: 1px solid var(--border); color: var(--text); border-radius: 4px;">
                <button type="submit" class="btn" style="font-size: 0.85rem; padding: 0.5rem 1.25rem;">Save Title</button>
            </form>
        </div>
        
        <div class="editor-layout">
            
            <!-- Question List Left Panel -->
            <div class="card" style="max-height: 80vh; overflow-y: auto;">
                <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1.5rem;">{db_title}</h3>
                {questions_list_html}
            </div>
            
            <!-- Question Form Right Panel -->
            <div class="card">
                <h3 style="border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; margin-bottom: 1.5rem;">{form_title}</h3>
                <form action="/save" method="POST">
                    {hidden_id_input}
                    <input type="hidden" name="file" value="{editing_file}">
                    
                    <div class="input-group">
                        <label class="input-label" for="question">{self.t['label_question_text']}</label>
                        <textarea id="question" name="question" rows="4" required placeholder="{self.t['placeholder_question_text']}">{form_q_text}</textarea>
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label" for="choice_A">{self.t['label_choice_a']}</label>
                        <input type="text" id="choice_A" name="choice_A" required value="{form_choice_A}" placeholder="{self.t['placeholder_choice_a']}">
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label" for="choice_B">{self.t['label_choice_b']}</label>
                        <input type="text" id="choice_B" name="choice_B" required value="{form_choice_B}" placeholder="{self.t['placeholder_choice_b']}">
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label" for="choice_C">{self.t['label_choice_c']}</label>
                        <input type="text" id="choice_C" name="choice_C" required value="{form_choice_C}" placeholder="{self.t['placeholder_choice_c']}">
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label" for="choice_D">{self.t['label_choice_d']}</label>
                        <input type="text" id="choice_D" name="choice_D" required value="{form_choice_D}" placeholder="{self.t['placeholder_choice_d']}">
                    </div>
                    
                    <div class="input-group">
                        <label class="input-label" for="correct">{self.t['label_correct_choice']}</label>
                        <select id="correct" name="correct" required>
                            <option value="A" {form_correct_options["A"]}>A</option>
                            <option value="B" {form_correct_options["B"]}>B</option>
                            <option value="C" {form_correct_options["C"]}>C</option>
                            <option value="D" {form_correct_options["D"]}>D</option>
                        </select>
                    </div>
                    
                    <div class="input-group" style="margin-bottom: 2rem;">
                        <label class="input-label" for="timeout_override">{self.t['label_timeout_override']}</label>
                        <input type="number" id="timeout_override" name="timeout_override" min="0" value="{form_timeout_override}" placeholder="{self.t['placeholder_timeout_override']}">
                        <small style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.25rem; display: block;">{self.t['timeout_override_hint']}</small>
                    </div>
                    
                    <button type="submit" class="btn" style="width: 100%;">{self.t['btn_save_question']}</button>
                    {cancel_btn}
                </form>
            </div>
            
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

def run_server(port=8083):
    """
    Main runner to start the question editor HTTP Server.
    """
    server_address = ("", port)
    httpd = HTTPServer(server_address, EditorAppHandler)
    print(f"Editor app started on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
