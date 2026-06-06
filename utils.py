import os
import json
import hashlib
import uuid
import time
import http.server
import traceback
from http.cookies import SimpleCookie
from urllib.parse import parse_qs

# =====================================================================
# ATOMIC JSON OPERATIONS
# =====================================================================

def load_json(path, default=None):
    """
    Safely load JSON data from a file. If the file does not exist,
    returns the specified default value.
    """
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return default

def save_json(path, data):
    """
    Atomically save JSON data to a file by writing to a temporary file
    and replacing the original file.
    """
    dir_name = os.path.dirname(path)
    if dir_name and not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    
    tmp_path = path + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # Atomic replacement
        os.replace(tmp_path, path)
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except IOError:
                pass
        raise e

# =====================================================================
# CRYPTOGRAPHY & ID GENERATION
# =====================================================================

def hash_password(password):
    """
    Returns the SHA-256 hex digest of the password.
    """
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def generate_session_id():
    """
    Generates a secure unique session ID.
    """
    return uuid.uuid4().hex

# =====================================================================
# IN-MEMORY SESSION STORE
# =====================================================================

class SessionStore:
    """
    In-memory session manager with an idle timeout.
    """
    def __init__(self, expiry_seconds=1800):
        self.sessions = {}  # session_id -> dict
        self.expiry_seconds = expiry_seconds

    def get(self, session_id):
        """
        Retrieves active session and updates its last activity time.
        Returns None if session is expired or not found.
        """
        if not session_id or session_id not in self.sessions:
            return None
        sess = self.sessions[session_id]
        if time.time() - sess.get("last_activity", 0) > self.expiry_seconds:
            del self.sessions[session_id]
            return None
        sess["last_activity"] = time.time()
        return sess

    def create(self, username):
        """
        Creates a new session for a user.
        """
        session_id = generate_session_id()
        self.sessions[session_id] = {
            "session_id": session_id,
            "username": username,
            "last_activity": time.time()
        }
        return self.sessions[session_id]

    def delete(self, session_id):
        """
        Deletes a session.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

# =====================================================================
# BASE HTTP REQUEST HANDLER
# =====================================================================

class BaseHandler(http.server.BaseHTTPRequestHandler):
    """
    A custom HTTP handler extending BaseHTTPRequestHandler with helper
    methods for handling HTML, redirects, cookies, and error pages.
    """
    
    def send_html(self, content, status=200):
        """
        Sends a complete UTF-8 HTML response, disabling browser caching.
        """
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        
        encoded = content.encode("utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def redirect(self, path, status=302):
        """
        Redirects the browser to a specific URL path.
        """
        self.send_response(status)
        self.send_header("Location", path)
        self.end_headers()

    def send_response(self, code, message=None):
        """
        Overrides send_response to write status line first, followed by
        any buffered cookies.
        """
        super().send_response(code, message)
        if hasattr(self, "_cookies_to_set"):
            for cookie in self._cookies_to_set:
                for header in cookie.output().split("\r\n"):
                    if header:
                        k, v = header.split(":", 1)
                        self.send_header(k.strip(), v.strip())

    def get_cookie(self, name):
        """
        Retrieves a cookie value from the request headers.
        """
        cookie_header = self.headers.get("Cookie")
        if not cookie_header:
            return None
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
        except Exception:
            return None
        morsel = cookie.get(name)
        return morsel.value if morsel else None

    def set_cookie(self, name, value, max_age=1800, path="/"):
        """
        Buffers a secure HTTP-Only cookie to be sent during send_response.
        """
        if not hasattr(self, "_cookies_to_set"):
            self._cookies_to_set = []
        cookie = SimpleCookie()
        cookie[name] = value
        cookie[name]["path"] = path
        if max_age is not None:
            cookie[name]["max-age"] = max_age
        cookie[name]["httponly"] = True
        cookie[name]["samesite"] = "Lax"
        self._cookies_to_set.append(cookie)

    def parse_post_body(self):
        """
        Parses a URL-encoded POST request body.
        """
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length).decode("utf-8")
            parsed = parse_qs(body)
            # Flatten list values into single strings
            return {k: v[0] for k, v in parsed.items()}
        except Exception:
            return {}

    def get_session(self, session_store):
        """
        Retrieves the session for the current request, or None if invalid.
        """
        session_id = self.get_cookie("session_id")
        return session_store.get(session_id)

    def send_error_500(self, error):
        """
        Sends a standard formatted 500 error page with traceback.
        """
        tb = traceback.format_exc()
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>500 Internal Server Error</title>
    <style>
        body {{
            background-color: #0f0f0f;
            color: #ef4444;
            font-family: 'IBM Plex Mono', monospace;
            padding: 3rem;
            margin: 0;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #1a1a1a;
            border: 1px solid #ef4444;
            border-radius: 8px;
            padding: 2rem;
            box-shadow: 0 4px 10px rgba(239, 68, 68, 0.2);
        }}
        h1 {{ margin-top: 0; font-size: 1.8rem; color: #ef4444; }}
        pre {{
            background: #0f0f0f;
            color: #e5e5e5;
            padding: 1.5rem;
            border-radius: 4px;
            overflow-x: auto;
            border: 1px solid #333;
            font-size: 0.9rem;
            white-space: pre-wrap;
        }}
        a {{
            color: #f59e0b;
            text-decoration: none;
            display: inline-block;
            margin-top: 1.5rem;
        }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>500 Internal Server Error</h1>
        <p>An unexpected exception occurred on the server:</p>
        <pre>{tb}</pre>
        <a href="/">Go Back to Home</a>
    </div>
</body>
</html>"""
        try:
            self.send_html(html, status=500)
        except Exception:
            pass

    def handle_one_request(self):
        """
        Overrides http.server's dispatcher to catch all exceptions in handlers
        and display a beautiful 500 internal server error page.
        """
        try:
            self.raw_requestline = self.rfile.readline(65537)
            if len(self.raw_requestline) > 65536:
                self.requestline = ''
                self.request_version = ''
                self.command = ''
                self.send_error(414)
                return
            if not self.raw_requestline:
                self.close_connection = True
                return
            if not self.parse_request():
                return
            mname = 'do_' + self.command
            if not hasattr(self, mname):
                self.send_error(501, f"Unsupported method ({self.command!r})")
                return
            method = getattr(self, mname)
            try:
                method()
                self.wfile.flush()
            except Exception as e:
                self.send_error_500(e)
        except Exception as e:
            try:
                self.send_error_500(e)
            except Exception:
                pass


# =====================================================================
# MULTI-LANGUAGE TRANSLATION SYSTEM
# =====================================================================

def get_translations():
    """
    Reads the active language from config.json, loads the matching json translation file,
    and returns a merged dictionary with language_en.json as a fallback.
    """
    config = load_json("data/config.json", {})
    lang = config.get("language", "en")
    
    # Load default (English) translations
    en_translations = load_json("data/language_en.json", {})
    
    if lang == "en":
        return "en", en_translations
        
    # Load specific language translations
    lang_file = f"data/language_{lang}.json"
    translations = load_json(lang_file, {})
    
    # Merge specific language over English defaults to avoid missing keys
    merged = {**en_translations, **translations}
    return lang, merged

def get_available_languages():
    """
    Scans the data directory dynamically for language_*.json files and returns a list
    of dictionaries with language code and localized language name.
    """
    available = []
    data_dir = "data"
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.startswith("language_") and filename.endswith(".json"):
                # Extract language code (e.g. language_en.json -> en)
                parts = filename.split("_")
                if len(parts) >= 2:
                    code = parts[1].split(".")[0]
                    lang_data = load_json(os.path.join(data_dir, filename), {})
                    name = lang_data.get("lang_name", code)
                    available.append({"code": code, "name": name})
    
    # Ensure English is at least returned if no files found
    if not available:
        available = [{"code": "en", "name": "English"}]
    else:
        # Sort so English is always first, then others alphabetically
        available.sort(key=lambda x: (0 if x["code"] == "en" else 1, x["name"]))
    return available

def get_translated_message(msg_param, translations):
    """
    Checks if a status message corresponds to a translation key. Supports parameters
    delimited by a colon (e.g., 'msg_user_created:username' or 'err_question_not_found_id:q001').
    """
    if not msg_param:
        return ""
    
    if ":" in msg_param:
        key, val = msg_param.split(":", 1)
        if key in translations:
            try:
                return translations[key].format(username=val, id=val)
            except (KeyError, ValueError):
                pass
        # Fallback to key if formatting fails
        if key in translations:
            return translations[key]
            
    if msg_param in translations:
        return translations[msg_param]
        
    return msg_param


# =====================================================================
# QUESTIONS FILE MANAGEMENT HELPERS
# =====================================================================

def get_active_questions_file():
    """
    Reads the active questions file setting from config.json.
    Defaults to 'question_00.json'.
    """
    config = load_json("data/config.json", {})
    return config.get("questions_file", "question_00.json")

def get_available_questions_files():
    """
    Scans the data directory dynamically for question_*.json files.
    """
    available = []
    data_dir = "data"
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.startswith("question_") and filename.endswith(".json"):
                available.append(filename)
    
    if not available:
        available = ["question_00.json"]
    else:
        # Sort alphabetically
        available.sort()
    return available

