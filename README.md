# Python Multi-Service Quiz Platform

A modern, responsive, and completely self-contained quiz platform built using **only the Python standard library**. It utilizes zero external dependencies (no Flask, no Django, no Pip packages) and follows a beautiful consistent dark theme featuring the **IBM Plex Mono** font.

---

## System Overview

The platform consists of three independent web services running on separate ports:

1. **Student Quiz Portal** (Port `8080`): Handles student authentication, quiz sessions, JS countdown timers, backend timeout validation, and score records.
2. **Admin Panel** (Port `8081`): Allows student account management, password resets, database stats inspection, and full scorecard visualization.
3. **Question Editor** (Port `8083`): Single-page database management interface to create, update, or delete quiz questions.

---

## Installation & Setup

Since the platform uses only the Python standard library, there is no package installation step (`pip install` is not required).

### Prerequisites
- Python 3.8 or higher.
- Note: On most Unix/macOS environments, run commands using `python3` instead of `python` (which might be unassigned).

### Step 1: Initialize the Database
Run the setup script to create the necessary directories and default configuration/user/question databases:

```bash
python3 setup.py
```

This command will:
- Create `/data/` and `/data/scorecards/` subdirectories.
- Write a default global config in `data/config.json`.
- Populate a set of photography questions in `data/questions.json`.
- Set up initial users in `data/users.json` (1 administrator, 2 students).

---

## How to Run

You can launch the entire ecosystem concurrently or run each component independently.

### Option A: Run All Services Together (Recommended)
Launch the threaded startup coordinator script:

```bash
python3 start_all.py
```

This will run all three servers simultaneously. Press `Ctrl+C` to shut down all servers gracefully.

### Option B: Run Services Independently
If you want to run only a specific component or test them in separate shell windows, run:

```bash
# Start Student Quiz App (Port 8080)
python3 quiz_app.py

# Start Admin Management Panel (Port 8081)
python3 admin_app.py

# Start Question Editor (Port 8083)
python3 editor_app.py
```

---

## Script Walkthrough

### 1. `setup.py`
The initialization script. Run this first to generate the template databases.

### 2. `utils.py`
Shared library containing core backend utilities:
- **Atomic Operations**: `load_json` and `save_json` write to temporary files first (`.tmp`) before moving them to prevent database corruption.
- **Session Handler**: `SessionStore` implements cookie-based sessions with a 30-minute idle timeout.
- **BaseHandler**: Extends standard `BaseHTTPRequestHandler` to support cookie-buffering (ensuring correct HTTP status header sequence) and unhandled exception catchers (delivering a clean 500 error page).

### 3. `quiz_app.py` (Port 8080)
The client-facing portal.
- **Access**: `http://localhost:8080`
- **Default Accounts**: 
  - Username: `student1` | Password: `pass1234`
  - Username: `student2` | Password: `pass1234`
- **Dynamic Quiz Title**: Resolves and displays the correct user-defined quiz label/title dynamically based on the active questions file specified in the configuration.
- **Timer**: A countdown timer is displayed for active question limits. It turns red in under 10 seconds and auto-submits on expiration.
- **Anti-Cheat**: If a student refreshes or stops Javascript, the backend checks the elapsed time against `start_time_of_current_question` stored in the session and marks it as a timeout if exceeded.

### 4. `admin_app.py` (Port 8081)
The dashboard for staff.
- **Access**: `http://localhost:8081`
- **Default Account**: 
  - Username: `admin` | Password: `admin123`
- **Features**: View submission logs, check student success percentages, view question-by-question student scorecards, reset student credentials, or add/delete student profiles. Includes quiz labels alongside quiz filenames in the settings selection dropdown.

### 5. `editor_app.py` (Port 8083)
A single-page, split-panel questions dashboard.
- **Access**: `http://localhost:8083` (No auth required).
- **Features**: Add, modify, or delete questions. ID allocation (e.g., `q001`, `q002`...) is automatically incremented.
- **Quiz Labeling**: Allows defining and saving a customized title/label for each individual quiz file (stored in `data/config.json`), which displays next to the filename in dropdown selection menus across services.
