# ABC-Quiz

[English](#abc-quiz) | [繁體中文](#abc-quiz-繁體中文)

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

---

# ABC-Quiz (繁體中文)

[English](#abc-quiz) | [繁體中文](#abc-quiz-繁體中文)

一個現代、響應式且完全自包含的測驗平台，**僅使用 Python 標準庫**構建。它不需要任何外部依賴（無 Flask、無 Django、無需 Pip 安裝包），並採用基於 **IBM Plex Mono** 字型的精美一致深色主題。

---

## 系統概述

本平台由三個運行在不同連接埠（Port）的獨立網頁服務組成：

1. **學生測驗入口網站**（連接埠 `8080`）：處理學生身分驗證、測驗工作階段、JS 倒數計時器、後端逾時驗證及分數記錄。
2. **管理員控制面板**（連接埠 `8081`）：允許管理學生帳戶、重設密碼、檢查資料庫統計資訊以及完整計分卡視覺化展示。
3. **題目編輯器**（連接埠 `8083`）：單頁式資料庫管理介面，用於新增、更新或刪除測驗題目。

---

## 安裝與設定

由於本平台僅使用 Python 標準庫，因此無需任何套件安裝步驟（不需要執行 `pip install`）。

### 系統需求
- Python 3.8 或更高版本。
- 注意：在大多數 Unix/macOS 環境中，請使用 `python3` 替代 `python` 執行指令（後者可能未分配路徑）。

### 步驟 1：初始化資料庫
執行設定指令碼以建立必要的目錄以及預設的設定、使用者和題目資料庫：

```bash
python3 setup.py
```

此指令將會：
- 建立 `/data/` 與 `/data/scorecards/` 子目錄。
- 在 `data/config.json` 中寫入預設的全域設定。
- 在 `data/questions.json` 中填入一組攝影相關題目。
- 在 `data/users.json` 中設定初始使用者（1 位管理員，2 位學生）。

---

## 如何執行

您可以同時啟動整個生態系統，或是獨立執行每個組件。

### 方案 A：同時執行所有服務（推薦）
啟動多執行緒啟動協調指令碼：

```bash
python3 start_all.py
```

這將同時執行所有三個伺服器。按下 `Ctrl+C` 即可優雅地關閉所有伺服器。

### 方案 B：獨立執行各個服務
如果您只想執行特定組件，或是在不同的終端機視窗中進行測試，請執行：

```bash
# 啟動學生測驗應用程式 (連接埠 8080)
python3 quiz_app.py

# 啟動管理員管理面板 (連接埠 8081)
python3 admin_app.py

# 啟動題目編輯器 (連接埠 8083)
python3 editor_app.py
```

---

## 指令碼與核心模組說明

### 1. `setup.py`
初始化指令碼。請先執行此指令碼以產生資料庫範本。

### 2. `utils.py`
包含核心後端公用程式的共享程式庫：
- **不可分割操作 (Atomic Operations)**：`load_json` 和 `save_json` 會先寫入暫存檔案（`.tmp`）然後再進行移轉，以防止資料庫損壞。
- **工作階段管理器 (Session Handler)**：`SessionStore` 實作了基於 Cookie 的工作階段（Session），並設有 30 分鐘的閒置逾時限制。
- **BaseHandler**：擴充了標準的 `BaseHTTPRequestHandler`，以支援 Cookie 快取（確保正確的 HTTP 狀態標頭順序）與未處理例外狀況的擷取器（呈現乾淨的 500 錯誤頁面）。

### 3. `quiz_app.py` (連接埠 8080)
面向用戶端的入口網站。
- **存取網址**：`http://localhost:8080`
- **預設帳戶**：
  - 使用者名稱：`student1` | 密碼：`pass1234`
  - 使用者名稱：`student2` | 密碼：`pass1234`
- **動態測驗標題**：根據設定中指定的活動題目檔案，動態解析並顯示正確的使用者自訂測驗標籤/標題。
- **計時器**：顯示當前題目時間限制的倒數計時器。在剩餘時間少於 10 秒時會變紅，並在逾時後自動送出答案。
- **防作弊機制**：如果學生重新整理頁面或停用 JavaScript，後端會比對目前時間與儲存在工作階段（Session）中的 `start_time_of_current_question`，若超過時限則標記為逾時。

### 4. `admin_app.py` (連接埠 8081)
教職員管理控制台。
- **存取網址**：`http://localhost:8081`
- **預設帳戶**：
  - 使用者名稱：`admin` | 密碼：`admin123`
- **功能**：查看提交記錄、檢查學生成績百分比、逐題查看學生計分卡、重設學生登入憑證，以及新增/刪除學生設定檔。在設定選擇下拉選單中同時顯示測驗標籤與測驗檔案名稱。

### 5. `editor_app.py` (連接埠 8083)
單頁式、雙面板設計的題目管理主控台。
- **存取網址**：`http://localhost:8083`（無需身份驗證）。
- **功能**：新增、修改或刪除題目。ID 分配（例如：`q001`、`q002` 等）會自動遞增。
- **測驗標籤設定**：允許為每個獨立的測驗檔案（儲存在 `data/config.json` 中）定義並儲存自訂的標題/標籤，該標籤會在各個服務的下拉選擇選單中顯示於檔案名稱旁。
