# Quick Testing Guide

## Step 1: Run Setup Test

```bash
python scripts/test_ui_setup.py
```

This will verify:
- ✅ All imports work
- ✅ File structure is correct
- ✅ Rule catalog exists
- ✅ Configuration is available
- ✅ Database connection works
- ✅ Run directories can be created

## Step 2: Start the UI

```bash
streamlit run planproof/ui/main.py
```

The browser should open automatically at `http://localhost:8501`

## Step 3: Test Upload

1. **Upload Page** (default):
   - Enter application reference: `TEST-001`
   - Upload a PDF file
   - Click "Process Documents"

2. **Expected**: 
   - Redirects to Status page
   - Shows processing progress
   - Run ID is displayed

## Step 4: Monitor Status

1. **Status Page**:
   - Should show "🔄 Processing in Progress..."
   - Progress bar updates
   - Current file name displayed
   - Auto-refreshes every 2 seconds

2. **Wait for completion**:
   - Status changes to "✅ Processing Completed"
   - "View Results" button appears

## Step 5: View Results

1. **Results Page**:
   - Summary cards show counts
   - Validation findings listed
   - Expand findings to see evidence
   - Export buttons available

2. **Test Export**:
   - Click "Download JSON" - verify file downloads
   - Click "Download Run Bundle (ZIP)" - verify ZIP contains files

## Troubleshooting

### If UI doesn't start:
```bash
# Check PYTHONPATH
export PYTHONPATH="$PWD"  # Linux/Mac
$env:PYTHONPATH="$PWD"    # Windows PowerShell

# Then try again
streamlit run planproof/ui/main.py
```

### If processing fails:
- Check terminal for error messages
- Verify rule catalog: `python scripts/build_rule_catalog.py`
- Check database connection: `python scripts/check_db.py`
- Verify Azure services are accessible

### If files don't appear:
- Check `./runs/` directory is created
- Verify write permissions
- Check terminal for file save errors

## Expected Test Results

✅ **All Good**: UI starts, upload works, processing completes, results display

⚠️ **Partial**: UI starts but processing fails - check error messages

❌ **Not Working**: UI doesn't start - check setup test output

