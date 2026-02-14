# Job Tracker

A Python CLI application to track your job applications during a job search.

## Features

- **Add** job applications with company, position, status, dates, salary, location, and notes
- **List** all applications with optional status filter
- **View** detailed information for any application
- **Update** application status and other fields
- **Search** by company name, position, or notes
- **Statistics** dashboard showing your pipeline by status
- **Persistent storage** using SQLite (no setup required)

## Status Workflow

Applications move through these stages: `wishlist` → `applying` → `applied` → `interviewing` → `offer` → `accepted` or `rejected`

## Setup

1. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate    # Windows
   # or: source venv/bin/activate  # macOS/Linux
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python main.py
   ```

## Launch the Windows App

```bash
python main.py gui
# or
python run_gui.py
```

The GUI provides a modern desktop interface with:
- Job list table with status filter
- Add / Edit / Delete jobs via dialogs
- Statistics bar
- Dark theme by default

## CLI Usage Examples

```bash
# Add a new application
python main.py add "Acme Corp" "Software Engineer" -s applied -u "https://..."
python main.py add "TechCo" "Data Scientist" -s wishlist -l "Remote"

# List all jobs (or filter by status)
python main.py list
python main.py list -s interviewing

# View job details
python main.py show 1

# Update status
python main.py update 1 -s offer

# Search
python main.py search "engineer"

# View statistics
python main.py stats

# Delete a job
python main.py delete 1
```

## Data Storage

All data is stored in `jobs.db` (SQLite) in the project directory. You can backup or move this file to preserve your data.
