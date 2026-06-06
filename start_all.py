import os
import threading
import time
import sys
from http.server import HTTPServer

# Import handlers and utilities from our self-contained modules
from quiz_app import QuizAppHandler
from admin_app import AdminAppHandler
from editor_app import EditorAppHandler
from setup import run_setup

def main():
    print("=========================================================")
    print("           STARTING QUIZ PLATFORM CHANNELS               ")
    print("=========================================================")

    # 1. Self-healing: Run setup if data directory or user accounts are missing
    if not os.path.exists("data") or not os.path.exists("data/users.json"):
        print("Data directories or config files not found. running auto-setup...")
        run_setup()
        print("-" * 57)
    else:
        # Migration logic for questions file
        if os.path.exists("data/questions.json") and not os.path.exists("data/question_00.json"):
            try:
                os.rename("data/questions.json", "data/question_00.json")
                print("[+] Migrated data/questions.json -> data/question_00.json")
            except Exception as e:
                print(f"[-] Migration failed: {e}")
                
        # Make sure questions_file is configured in config.json
        from utils import load_json, save_json
        config = load_json("data/config.json", {})
        if "questions_file" not in config:
            config["questions_file"] = "question_00.json"
            save_json("data/config.json", config)
            print("[+] Added questions_file setting to config.json")

    servers = []
    configs = [
        {"name": "Student Quiz App", "port": 8080, "handler": QuizAppHandler},
        {"name": "Admin Portal    ", "port": 8081, "handler": AdminAppHandler},
        {"name": "Question Editor ", "port": 8083, "handler": EditorAppHandler}
    ]

    # 2. Launch servers in daemon threads
    for conf in configs:
        try:
            httpd = HTTPServer(("", conf["port"]), conf["handler"])
            servers.append((conf["name"], httpd))

            def serve(server=httpd, name=conf["name"], port=conf["port"]):
                try:
                    server.serve_forever()
                except Exception as e:
                    print(f"\n[-] Error in {name} thread: {e}")

            t = threading.Thread(target=serve)
            t.daemon = True
            t.start()
            print(f"[+] {conf['name']} running on -> http://localhost:{conf['port']}")
        except Exception as e:
            print(f"[-] Failed to bind server {conf['name']} on port {conf['port']}: {e}")
            # Shutdown any already started servers before exiting
            for name, server in servers:
                server.shutdown()
                server.server_close()
            sys.exit(1)

    print("=========================================================")
    print("All services are live. Press [Ctrl+C] to stop all servers.")
    print("=========================================================")

    # 3. Main thread wait loop with graceful signal handling
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n[!] KeyboardInterrupt received. Initiating graceful shutdown...")
        
        # Call shutdown on each HTTP server to stop serving immediately
        for name, server in servers:
            print(f"[-] Shutting down {name}...")
            # shutdown() stops serve_forever loop safely across threads
            server.shutdown()
            server.server_close()
            
        print("[+] All services halted. Execution finished successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
