# Latein Vokabeltrainer (Flask Version)

This is a full-stack version of the vocabulary trainer with user accounts and progress tracking.

## Setup & Run

1.  **Double-click `run_app.bat`** in the root folder.
    *   This will automatically create a virtual environment, install dependencies, and start the server.
2.  Open your browser and go to `http://127.0.0.1:5000`.

## First Time Setup

1.  **Register** a new account.
2.  **Login**.
3.  To import your existing vocabulary files (`L14.json`, etc.), go to: `http://127.0.0.1:5000/import_data` while logged in.
    *   You should see a message saying how many words were imported.
4.  Go back to the home page (`/`) and start learning!

## Features

*   **User Accounts**: Individual progress tracking.
*   **Smart Learning**:
    *   Selects 70% words you struggle with and 30% words you know well.
    *   Tracks your last 3 attempts to calculate confidence.
*   **Keyboard Controls**:
    *   `Space`: Reveal translation.
    *   `Arrow Up`: Mark as Correct.
    *   `Arrow Down`: Mark as Wrong.
