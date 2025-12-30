# Understanding Blob URIs and Extracted Data

## What is a Blob URI?

A **blob URI** is a reference to a file stored in **Azure Blob Storage** (cloud file storage).

### Format
```
azure://<storage_account>/<container>/<blob_name>
```

### Example Breakdown
```
azure://planproofdevstg86723/artefacts/extracted_layout_79_20251230_034328.json
```

- **Storage Account:** `planproofdevstg86723`
- **Container:** `artefacts` (folder in blob storage)
- **Blob Name:** `extracted_layout_79_20251230_034328.json` (the actual file)

## Where is the Data?

The **actual JSON data is stored in Azure Blob Storage**, not in PostgreSQL. The database only stores:
- The blob URI (reference/link to the file)
- Metadata about the file
- When it was created

## What's in the JSON Files?

### 1. `extracted_layout_*.json` (Raw Document Intelligence Output)

Contains the raw extraction from Azure Document Intelligence:

```json
{
  "metadata": {
    "model": "prebuilt-layout",
    "page_count": 4,
    "analyzed_at": null
  },
  "text_blocks": [
    {
      "content": "4 DURLSTON GROVE",
      "page_number": 1,
      "bounding_box": {...},
      "role": null
    },
    {
      "content": "LOFT WITH CONVERSION WITH DORMER WINDOWS...",
      "page_number": 1,
      ...
    }
    // ... 159 text blocks total
  ],
  "tables": [],
  "page_anchors": {
    "1": {
      "text_blocks": [...],
      "tables": []
    },
    "2": {...}
  }
}
```

**Size:** ~107 KB for a 4-page document

### 2. `extraction_*.json` (Mapped Fields + Evidence)

Contains structured fields extracted by the field mapper:

```json
{
  "fields": {
    "document_type": "site_plan",
    "site_address": "4 DURLSTON GROVE",
    "proposed_use": "LOFT WITH CONVERSION WITH DORMER WINDOWS AND CONVERSION TO HMO USE.",
    "applicant_phone": null
  },
  "evidence_index": {
    "site_address": [
      {
        "page": 1,
        "block_id": "p1b0",
        "snippet": "4 DURLSTON GROVE"
      }
    ],
    "proposed_use": [
      {
        "page": 1,
        "block_id": "p1b1",
        "snippet": "LOFT WITH CONVERSION..."
      }
    ],
    "text_block_0": {
      "type": "text_block",
      "content": "4 DURLSTON GROVE",
      "snippet": "4 DURLSTON GROVE",
      "page_number": 1
    }
    // ... more evidence entries
  },
  "metadata": {...},
  "text_blocks": [...],
  "tables": [...]
}
```

### 3. `validation_*.json` (Validation Results)

Contains rule validation results:

```json
{
  "summary": {
    "rule_count": 3,
    "pass": 2,
    "needs_review": 1,
    "fail": 0,
    "needs_llm": false
  },
  "findings": [
    {
      "rule_id": "R1",
      "severity": "error",
      "status": "pass",
      "message": "All required fields present.",
      "required_fields": ["site_address"],
      "missing_fields": [],
      "evidence": {
        "expected_sources": ["application_form", "site_plan"],
        "keywords": ["address", "postcode"],
        "evidence_snippets": [...]
      }
    }
    // ... more findings
  ]
}
```

## How to View the JSON Content

### Option 1: Using Python Script
```bash
python scripts/view_blob_json.py "azure://planproofdevstg86723/artefacts/extracted_layout_79_20251230_034328.json"
```

### Option 2: Download via Python
```python
from planproof.storage import StorageClient
import json

sc = StorageClient()
data = sc.download_blob("artefacts", "extracted_layout_79_20251230_034328.json")
result = json.loads(data.decode("utf-8"))
print(json.dumps(result, indent=2))
```

### Option 3: Azure Portal
1. Go to Azure Portal → Storage Account → `planproofdevstg86723`
2. Navigate to Containers → `artefacts`
3. Find the file: `extracted_layout_79_20251230_034328.json`
4. Click "Download" or "Edit" to view

## Why Store in Blob Storage?

1. **Scalability:** JSON files can be large (100KB+ per document)
2. **Cost:** Blob storage is cheaper than database storage for large files
3. **Performance:** Database stays fast, large files don't slow it down
4. **Flexibility:** Easy to access files directly without database queries

## Summary

- **Blob URI** = Address/link to a file in Azure Blob Storage
- **Database** = Stores metadata and blob URIs (not the actual JSON)
- **Blob Storage** = Stores the actual JSON files
- **extracted_layout** = Raw Document Intelligence output (text blocks, tables, layout)
- **extraction** = Mapped fields + evidence index
- **validation** = Rule validation results

