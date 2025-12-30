# Application Status: 202506361PA

## Summary

**Application Reference:** 202506361PA  
**Application ID:** 2  
**Applicant:** Shaji  
**Created:** 2025-12-30 06:04:25

## Current Status

### Documents
- **Total:** 3 documents uploaded
- **Processed:** 0 documents (none have been processed yet)
- **Documents:**
  1. Document-DEA8A9AF4764ABA5965D620017BCD119.pdf (ID: 83)
     - Uploaded: 2025-12-30 06:10:54
     - Status: Not processed
  2. Document-92C2F0E3D233D9722023BD0BAA17C379.pdf (ID: 82)
     - Uploaded: 2025-12-30 06:07:19
     - Status: Not processed
  3. Document-8B3727462503AC2C6EB3A930DDC04D92.pdf (ID: 81)
     - Uploaded: 2025-12-30 06:04:30
     - Status: Not processed

### Submissions
- **Total:** 1 submission
- **V0 Submission** (ID: 2)
  - Status: pending
  - Created: 2025-12-30 06:04:26

### Runs
- **Total:** 0 runs found
- **Status:** No processing runs have been created for this application

## Issue

The documents were uploaded but **no processing runs were created**. This means:
- Documents are in the database
- But they haven't been processed (extraction, validation, etc.)

## Next Steps

To process these documents, you need to:
1. Run the processing pipeline on the documents
2. Or use the UI to upload and process them again

## Database Connection Error Fix

The "Address already in use" error has been fixed by:
- Adding connection pool limits (pool_size=5, max_overflow=10)
- Adding connection recycling (pool_recycle=3600)
- Adding connection verification (pool_pre_ping=True)
- Ensuring sessions are properly closed and connections returned to pool

The UI should now work without connection errors.

