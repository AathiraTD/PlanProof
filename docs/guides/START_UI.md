# How to Start the PlanProof UI

## Location

The UI files are located in:
```
planproof/ui/
├── main.py              ← Main entry point
├── run_orchestrator.py  ← Backend logic
└── pages/
    ├── upload.py        ← Upload page
    ├── status.py        ← Status page
    └── results.py       ← Results page
```

## Quick Start

### Step 1: Open Terminal

Navigate to the project root directory:
```bash
cd D:\Projects\plan-proof\PlanProof
```

### Step 2: Start the UI

Run this command:
```bash
streamlit run planproof/ui/main.py
```

### Step 3: Access the UI

The UI will automatically open in your browser at:
```
http://localhost:8501
```

If it doesn't open automatically, copy the URL from the terminal output.

## What You'll See

1. **Upload Page** (default):
   - Enter application reference
   - Upload PDF files
   - Click "Process Documents"

2. **Status Page**:
   - View processing progress
   - See current file being processed
   - Auto-refreshes every 2 seconds

3. **Results Page**:
   - View validation results
   - See findings with evidence
   - Export results

## Troubleshooting

### If you get "ModuleNotFoundError":

Set PYTHONPATH first:
```bash
# Windows PowerShell
$env:PYTHONPATH="$PWD"
streamlit run planproof/ui/main.py

# Windows CMD
set PYTHONPATH=%CD%
streamlit run planproof/ui/main.py

# Linux/Mac
export PYTHONPATH="$PWD"
streamlit run planproof/ui/main.py
```

### If streamlit is not installed:

```bash
pip install streamlit
```

### If the browser doesn't open:

1. Check the terminal for the URL (usually `http://localhost:8501`)
2. Copy and paste it into your browser manually

## Stop the UI

Press `Ctrl+C` in the terminal where Streamlit is running.

