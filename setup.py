import os
from utils import save_json, hash_password

def run_setup():
    """
    Initializes the directories and standard data files (config, questions, users)
    needed to run ABC-Quiz.
    """
    print("Initializing ABC-Quiz data files...")
    
    # 1. Create Directories
    data_dir = "data"
    scorecards_dir = os.path.join(data_dir, "scorecards")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(scorecards_dir, exist_ok=True)
    print(f"Created directories: {data_dir}/ and {scorecards_dir}/")

    # 2. Write global config.json
    config_path = os.path.join(data_dir, "config.json")
    config_data = {
        "quiz_title": "Photography Knowledge Quiz",
        "timeout_seconds": 30,
        "questions_per_session": 5,
        "allow_retake": True,
        "questions_file": "question_00.json"
    }
    save_json(config_path, config_data)
    print(f"Wrote configuration to: {config_path}")
 
    # 3. Write default question_00.json
    questions_path = os.path.join(data_dir, "question_00.json")
    questions_data = [
        {
            "id": "q001",
            "question": "What is a common mistake beginners make when using flash for the first time?",
            "choices": {
                "A": "Thinking the flash light can reach extremely far distances, like across a harbor.",
                "B": "Using too many batteries at once.",
                "C": "Setting the shutter speed to 1 second.",
                "D": "Forgetting to turn on the camera."
            },
            "correct": "A",
            "timeout_override": None
        },
        {
            "id": "q002",
            "question": "In manual exposure mode, what three primary elements make up the Exposure Triangle?",
            "choices": {
                "A": "Aperture, Shutter Speed, ISO",
                "B": "Focus, White Balance, Zoom",
                "C": "Resolution, Focal Length, Sensor Size",
                "D": "Flash Power, Ambient Light, Subject Distance"
            },
            "correct": "A",
            "timeout_override": None
        },
        {
            "id": "q003",
            "question": "Which aperture setting provides the shallowest depth of field, ideal for blurring portrait backgrounds?",
            "choices": {
                "A": "f/22",
                "B": "f/8",
                "C": "f/2.8",
                "D": "f/16"
            },
            "correct": "C",
            "timeout_override": None
        },
        {
            "id": "q004",
            "question": "Which shutter speed is most appropriate for freezing fast-moving sports or action shots?",
            "choices": {
                "A": "1/2000 second",
                "B": "1/30 second",
                "C": "1 second",
                "D": "1/4 second"
            },
            "correct": "A",
            "timeout_override": None
        },
        {
            "id": "q005",
            "question": "What is the primary visual byproduct of using a very high ISO setting in low-light photography?",
            "choices": {
                "A": "A shutter speed that is too fast.",
                "B": "Digital noise and grain in the image details.",
                "C": "An over-saturated color palette.",
                "D": "Chromatic aberration around high-contrast edges."
            },
            "correct": "B",
            "timeout_override": None
        },
        {
            "id": "q006",
            "question": "What does focal length (e.g. 50mm vs 200mm) determine in a camera lens?",
            "choices": {
                "A": "The speed at which the lens auto-focuses.",
                "B": "The physical length of the camera body.",
                "C": "The magnification and angle of view.",
                "D": "The amount of light reaching the sensor."
            },
            "correct": "C",
            "timeout_override": None
        }
    ]
    save_json(questions_path, questions_data)
    print(f"Wrote {len(questions_data)} sample questions to: {questions_path}")
 
    # 4. Write users.json
    users_path = os.path.join(data_dir, "users.json")
    users_data = [
        {
            "username": "student1",
            "password_hash": hash_password("pass1234"),
            "role": "student"
        },
        {
            "username": "student2",
            "password_hash": hash_password("pass1234"),
            "role": "student"
        },
        {
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": "admin"
        }
    ]
    save_json(users_path, users_data)
    print(f"Wrote user accounts (1 admin, 2 students) to: {users_path}")
    print("\nInitialization Complete! You can start the servers now:")
    print("  Port 8080: Student Quiz Site (quiz_app.py)")
    print("  Port 8081: Admin Dashboard (admin_app.py)")
    print("  Port 8083: Question Editor (editor_app.py)")
    print("Or run python start_all.py to launch all of them.")

if __name__ == "__main__":
    run_setup()
