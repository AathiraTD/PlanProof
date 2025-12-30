# Extraction Performance Analysis

## Current Bottlenecks

### 1. **Azure Document Intelligence API Call (MAJOR BOTTLENECK)**
- **Location**: `planproof/docintel.py` line 55-60
- **Issue**: `poller.result()` is **synchronous and blocking**
- **Time**: 5-30 seconds per document (depends on PDF size/complexity)
- **Impact**: This is the **primary bottleneck** - accounts for 80-90% of extraction time

### 2. **No Caching - Re-extracting Every Time**
- **Location**: `planproof/ui/run_orchestrator.py` line 155
- **Issue**: `extract_from_pdf_bytes()` always calls `docintel.analyze_document()` 
- **Problem**: Even if document was already extracted, it's re-extracted
- **Solution Available**: `get_extraction_result()` exists but isn't being used
- **Impact**: Wastes API calls and time on duplicate documents

### 3. **Sequential Processing**
- **Location**: `planproof/ui/run_orchestrator.py` line 129
- **Issue**: Documents processed one at a time in a `for` loop
- **Impact**: 3 documents × 10 seconds = 30 seconds total (vs. ~10 seconds if parallel)

### 4. **Multiple Database Writes Per Document**
- **Location**: `planproof/pipeline/extract.py` lines 205-332
- **Issue**: Writing pages, evidence, and extracted fields individually
- **Impact**: Adds 1-2 seconds per document

### 5. **File I/O Operations**
- **Location**: Multiple places
- **Issue**: Reading PDFs, writing JSON files
- **Impact**: Adds ~0.5 seconds per document

## Performance Breakdown (Estimated)

For a typical 3-document batch:
- **Document Intelligence API**: 3 × 10s = **30 seconds** (90%)
- **Database writes**: 3 × 1.5s = **4.5 seconds** (13%)
- **File I/O**: 3 × 0.5s = **1.5 seconds** (4%)
- **Field mapping/validation**: 3 × 0.3s = **0.9 seconds** (3%)
- **Total**: ~37 seconds

## Solutions

### Solution 1: Add Extraction Caching (HIGH IMPACT, EASY)
**Impact**: Eliminates redundant API calls
**Effort**: Low
**Time Saved**: 10-30 seconds per duplicate document

Check if document was already extracted before calling API:
```python
# Check for existing extraction first
existing_extraction = get_extraction_result(document_id, db=db)
if existing_extraction:
    # Use cached result
    extraction_result = existing_extraction
else:
    # New extraction
    extraction_result = docintel.analyze_document(pdf_bytes, model=model)
```

### Solution 2: Parallel Processing (MEDIUM IMPACT, MEDIUM EFFORT)
**Impact**: Processes multiple documents simultaneously
**Effort**: Medium
**Time Saved**: ~66% for 3-document batch (30s → 10s)

Use `concurrent.futures.ThreadPoolExecutor` or `asyncio`:
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(process_document, file_path) for file_path in file_paths]
    results = [f.result() for f in futures]
```

### Solution 3: Batch Database Writes (LOW IMPACT, MEDIUM EFFORT)
**Impact**: Reduces database round-trips
**Effort**: Medium
**Time Saved**: ~1 second per document

Write all pages/evidence/fields in bulk instead of individually.

### Solution 4: Async Document Intelligence Calls (HIGH IMPACT, HIGH EFFORT)
**Impact**: Can process other documents while waiting for API
**Effort**: High (requires async refactoring)
**Time Saved**: Significant for large batches

Use async/await with Azure SDK async methods.

## Recommended Implementation Order

1. **✅ Solution 1: Add Caching** (Do this first - biggest impact, easiest)
2. **Solution 2: Parallel Processing** (Do this second - good ROI)
3. **Solution 3: Batch DB Writes** (Nice to have)
4. **Solution 4: Async API** (Future optimization)

## Expected Performance After Fixes

**With caching only:**
- First run: ~37 seconds (same)
- Re-run with same docs: ~7 seconds (80% faster)

**With caching + parallel processing:**
- First run: ~12 seconds (67% faster)
- Re-run: ~4 seconds (89% faster)

