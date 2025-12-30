# PostgreSQL Query Guide for PlanProof

## Database Connection Details

- **Server:** `planproof-dev-pgflex-8016.postgres.database.azure.com`
- **Database:** `planning_validation`
- **Schema:** `public` (default)
- **Username:** `pgadmin`
- **Password:** (from `.env` file)

## Table Names

The following tables are available in the `planning_validation` database:

1. **applications** - Planning application records
2. **documents** - PDF documents uploaded for processing
3. **artefacts** - Extracted JSON artefacts (extraction, validation, LLM notes)
4. **runs** - Processing run audit trail
5. **validation_results** - (Optional) Detailed validation results

## Common Queries

### View All Applications
```sql
SELECT * FROM applications;
```

### View Recent Documents
```sql
SELECT 
    id, 
    application_id, 
    filename, 
    page_count, 
    processed_at,
    docintel_model
FROM documents 
ORDER BY uploaded_at DESC 
LIMIT 10;
```

### View Processing Runs
```sql
SELECT 
    id, 
    run_type, 
    status, 
    started_at, 
    completed_at,
    document_id,
    application_id
FROM runs 
ORDER BY started_at DESC;
```

### View Artefacts
```sql
SELECT 
    id, 
    document_id, 
    artefact_type, 
    created_at,
    blob_uri
FROM artefacts 
ORDER BY created_at DESC 
LIMIT 10;
```

### Count Documents by Application
```sql
SELECT 
    a.application_ref,
    COUNT(d.id) as document_count
FROM applications a
LEFT JOIN documents d ON a.id = d.application_id
GROUP BY a.id, a.application_ref;
```

### View Documents with Processing Status
```sql
SELECT 
    d.id,
    d.filename,
    d.page_count,
    d.processed_at,
    d.docintel_model,
    COUNT(a.id) as artefact_count
FROM documents d
LEFT JOIN artefacts a ON d.id = a.document_id
GROUP BY d.id, d.filename, d.page_count, d.processed_at, d.docintel_model
ORDER BY d.uploaded_at DESC;
```

### View Run Summary with Document Counts
```sql
SELECT 
    r.id,
    r.run_type,
    r.status,
    r.started_at,
    r.completed_at,
    r.run_metadata->>'summary' as summary
FROM runs r
WHERE r.run_type = 'batch_pdf'
ORDER BY r.started_at DESC
LIMIT 5;
```

### Find Documents by Content Hash (Deduplication)
```sql
SELECT 
    content_hash,
    COUNT(*) as duplicate_count,
    STRING_AGG(id::text, ', ') as document_ids
FROM documents
WHERE content_hash IS NOT NULL
GROUP BY content_hash
HAVING COUNT(*) > 1;
```

### View Latest Extraction Artefacts
```sql
SELECT 
    a.id,
    a.document_id,
    d.filename,
    a.artefact_type,
    a.created_at,
    a.artefact_metadata->>'model' as model
FROM artefacts a
JOIN documents d ON a.document_id = d.id
WHERE a.artefact_type = 'extracted_layout'
ORDER BY a.created_at DESC
LIMIT 10;
```

## How to Query in Your Database Tool

### Step 1: Navigate to the Correct Database
1. In the left panel, find and **expand** `planning_validation` database
2. Expand the `public` schema (or it may be under "Schemas" → "public")
3. Expand "Tables" to see all tables

### Step 2: Open a Query Window
- Right-click on the `planning_validation` database
- Select "New Query" or "Query" option
- Or use the query icon next to the database name

### Step 3: Run Queries
1. Type your SQL query in the query editor
2. Click "Run" or press F5
3. Results will appear in the results pane below

### Step 4: View Table Data
- Right-click on any table name (e.g., `applications`)
- Select "Select Top 1000 Rows" or similar option
- This will generate and run a `SELECT *` query automatically

## Table Schemas

### applications
- `id` (Integer, Primary Key)
- `application_ref` (String, Unique)
- `applicant_name` (String, Nullable)
- `application_date` (Date, Nullable)
- `created_at` (DateTime)
- `updated_at` (DateTime)

### documents
- `id` (Integer, Primary Key)
- `application_id` (Integer, Foreign Key → applications.id)
- `filename` (String)
- `blob_uri` (String, Unique)
- `content_hash` (String, Unique) - SHA256 hash for deduplication
- `page_count` (Integer, Nullable)
- `uploaded_at` (DateTime)
- `processed_at` (DateTime, Nullable)
- `docintel_model` (String, Nullable) - e.g., "prebuilt-layout"

### artefacts
- `id` (Integer, Primary Key)
- `document_id` (Integer, Foreign Key → documents.id)
- `artefact_type` (String) - e.g., "extraction", "validation", "llm_notes", "extracted_layout"
- `blob_uri` (String, Unique)
- `created_at` (DateTime)
- `artefact_metadata` (JSON, Nullable)

### runs
- `id` (Integer, Primary Key)
- `run_type` (String) - e.g., "single_pdf", "batch_pdf"
- `document_id` (Integer, Foreign Key → documents.id, Nullable)
- `application_id` (Integer, Foreign Key → applications.id, Nullable)
- `started_at` (DateTime)
- `completed_at` (DateTime, Nullable)
- `status` (String) - "running", "completed", "completed_with_errors", "failed"
- `error_message` (Text, Nullable)
- `run_metadata` (JSON, Nullable) - Includes resolved_fields cache, summary, etc.

## Tips

1. **Always use the `planning_validation` database**, not `postgres` (which is the system database)
2. **Tables are in the `public` schema** (default schema)
3. **Use LIMIT** when exploring large tables
4. **Check `run_metadata`** for JSON data stored in runs
5. **Use `artefact_metadata`** for JSON data in artefacts

