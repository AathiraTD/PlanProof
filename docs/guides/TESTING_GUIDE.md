# PlanProof UI Testing Guide

## Pre-Testing Checklist

### 1. Verify Dependencies

```bash
# Check if streamlit is installed
pip show streamlit

# If not, install it
pip install streamlit

# Verify all other dependencies
pip install -r requirements.txt
```

### 2. Verify Configuration

Ensure your `.env` file has all required variables:
- `AZURE_STORAGE_CONNECTION_STRING`
- `DATABASE_URL`
- `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT_NAME`
- `AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT`, `AZURE_DOCUMENT_INTELLIGENCE_API_KEY`

### 3. Verify Database Setup

```bash
# Check database connection
python scripts/check_db.py

# Ensure rule catalog exists
python scripts/build_rule_catalog.py
ls artefacts/rule_catalog.json
```

### 4. Verify Run Directories

The UI will create `./runs/` directory automatically, but you can verify write permissions:

```bash
mkdir -p runs/test
rm -rf runs/test
```

## Testing Steps

### Test 1: Start the UI

```bash
# From project root
streamlit run planproof/ui/main.py
```

**Expected:**
- Browser opens at `http://localhost:8501`
- Sidebar shows "PlanProof" title
- Navigation shows: Upload, Status, Results
- Upload page is displayed by default

**If it fails:**
- Check Python path: `export PYTHONPATH="$PWD"` (Linux/Mac) or `$env:PYTHONPATH="$PWD"` (Windows)
- Check for import errors in terminal
- Verify streamlit is installed: `pip install streamlit`

### Test 2: Upload Page

**Steps:**
1. Navigate to Upload page (should be default)
2. Enter application reference: `TEST-APP-001`
3. (Optional) Enter applicant name: `Test Applicant`
4. Upload a test PDF file

**Expected:**
- File uploader accepts PDF files
- Shows uploaded file name and size
- "Process Documents" button is enabled when app_ref and files are provided
- Button is disabled if either is missing

**Test Cases:**
- ✅ Upload single PDF
- ✅ Upload multiple PDFs
- ✅ Try to process without app_ref (should show error)
- ✅ Try to process without files (should show error)

### Test 3: Processing (Status Page)

**Steps:**
1. After clicking "Process Documents", should redirect to Status page
2. Status page should show run ID
3. Enable auto-refresh

**Expected:**
- Shows "🔄 Processing in Progress..."
- Progress bar appears for multi-file uploads
- Shows "X / Y documents processed"
- Shows current file being processed
- Auto-refreshes every 2 seconds

**Test Cases:**
- ✅ Single file processing (should complete quickly)
- ✅ Multiple file processing (should show progress)
- ✅ Check that run_id is stored in session state
- ✅ Verify files are saved to `./runs/<run_id>/inputs/`

### Test 4: Results Page

**Steps:**
1. Wait for processing to complete
2. Click "View Results" button (or navigate manually)
3. Enter run_id if needed

**Expected:**
- Summary cards show: Total Documents, Processed, Errors, LLM Calls
- Validation summary shows: PASS, NEEDS_REVIEW, FAIL counts
- Findings table/list is displayed
- Each finding is expandable
- Evidence snippets are shown

**Test Cases:**
- ✅ View results for completed run
- ✅ Filter findings by status (All/pass/needs_review/fail)
- ✅ Filter findings by severity (All/error/warning)
- ✅ Expand findings to see evidence
- ✅ Check error section if any errors occurred

### Test 5: Export Functionality

**Steps:**
1. On Results page, scroll to "Export Results" section
2. Click "Download JSON"
3. Click "Download Run Bundle (ZIP)"

**Expected:**
- JSON download contains full results
- ZIP bundle contains:
  - `inputs/` folder with uploaded PDFs
  - `outputs/` folder with artifacts
  - `results.json` file

**Test Cases:**
- ✅ Download JSON and verify structure
- ✅ Download ZIP and verify contents
- ✅ Check that ZIP can be extracted
- ✅ Verify all files are included

### Test 6: Error Handling

**Test Cases:**
- ✅ Process with invalid PDF (corrupted file)
- ✅ Process with missing rule catalog
- ✅ Process with database connection error
- ✅ Verify error messages are displayed
- ✅ Verify traceback is shown in expandable section
- ✅ Verify "Download Error Logs" button works

### Test 7: Navigation

**Test Cases:**
- ✅ Navigate between pages using sidebar
- ✅ Session state persists (run_id maintained)
- ✅ Can manually enter run_id on Status/Results pages
- ✅ Auto-redirect from Upload → Status works
- ✅ Auto-redirect from Status → Results works

## Quick Test Script

Run this to verify basic functionality:

```bash
python scripts/test_ui_setup.py
```

## Common Issues & Solutions

### Issue: "ModuleNotFoundError: No module named 'planproof'"

**Solution:**
```bash
export PYTHONPATH="$PWD"  # Linux/Mac
$env:PYTHONPATH="$PWD"    # Windows PowerShell
```

### Issue: "Rule catalog not found"

**Solution:**
```bash
python scripts/build_rule_catalog.py
```

### Issue: Streamlit page not loading

**Solution:**
- Check terminal for error messages
- Verify all imports work: `python -c "from planproof.ui.main import *"`
- Check that `planproof/ui/pages/__init__.py` exists

### Issue: Processing hangs

**Solution:**
- Check database connection
- Check Azure service availability
- Check terminal for error messages
- Verify rule catalog exists

### Issue: Files not saving to runs/ directory

**Solution:**
- Check write permissions in project directory
- Verify `./runs/` directory can be created
- Check disk space

## Performance Testing

### Test with different file sizes:
- Small PDF (< 1 MB)
- Medium PDF (1-10 MB)
- Large PDF (> 10 MB)

### Test with different file counts:
- Single file
- 5 files
- 10+ files

### Monitor:
- Processing time per document
- Memory usage
- LLM call count
- Database query performance

## Integration Testing

### Test Full Workflow:
1. Upload → Process → View Results → Export
2. Multiple runs in sequence
3. View results from previous runs
4. Process same files again (should handle deduplication)

## Browser Testing

Test in different browsers:
- Chrome/Edge
- Firefox
- Safari (if on Mac)

## Next Steps After Testing

If all tests pass:
1. ✅ UI is ready for user acceptance testing
2. ✅ Document any issues found
3. ✅ Create test data set for stakeholders
4. ✅ Prepare demo for validation officers

