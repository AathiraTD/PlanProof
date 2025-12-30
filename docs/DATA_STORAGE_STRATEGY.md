# Data Storage Strategy

## Hybrid Approach: JSON Artefacts + Relational Tables

PlanProof uses a **hybrid data storage strategy** that maintains both JSON artefacts in blob storage and relational tables in PostgreSQL. This design provides the benefits of both approaches.

## Storage Layers

### 1. JSON Artefacts (Blob Storage)
**Purpose:** Complete audit trail, full data preservation, easy export/debugging

**Stored in:** Azure Blob Storage (`artefacts` container)

**Artefacts:**
- **`extraction`** - Complete extraction result with:
  - All extracted `fields` (application_ref, site_address, proposed_use, etc.)
  - Full `evidence_index` (all text blocks, tables, field-specific evidence)
  - All `text_blocks` (complete content with bounding boxes)
  - All `tables` (complete table data with cells)
  - `metadata` (page count, model used, timestamps)

- **`validation`** - Complete validation result with:
  - All `findings` (per-rule validation results)
  - `summary` (counts, needs_llm flag)
  - Full evidence snippets and context

- **`llm_notes`** - Complete LLM interaction with:
  - Full request/response
  - Gate reason (why LLM was triggered)
  - All filled fields and citations

**Benefits:**
- ✅ Complete data preservation (nothing lost)
- ✅ Easy debugging (can download and inspect full JSON)
- ✅ Audit trail (exact state at processing time)
- ✅ Export-friendly (single JSON file per artefact)
- ✅ Version control friendly (can diff JSON files)

### 2. Relational Tables (PostgreSQL)
**Purpose:** Queryable, structured data for operations and reporting

**Stored in:** PostgreSQL database

**Tables:**
- **`Page`** - Individual page records (page_number, metadata)
- **`Evidence`** - Individual evidence records (evidence_key, snippet, content, page_id, bbox)
- **`ExtractedField`** - Individual field records (field_name, field_value, confidence, evidence_id, extractor)
- **`ValidationCheck`** - Individual validation check records (rule_id, status, explanation, evidence_ids)
- **`Submission`** - Submission versions (V0, V1+) with metadata (resolved_fields, llm_calls_per_submission)

**Benefits:**
- ✅ Queryable (SQL queries, joins, filters)
- ✅ Structured (normalized, referential integrity)
- ✅ Efficient (indexed, optimized for queries)
- ✅ Relationships (foreign keys, cascades)
- ✅ Reporting (aggregations, analytics)

## Data Flow

```
PDF → Extract → [Write to both]
                ├─→ JSON Artefact (blob storage) - Complete data
                └─→ Relational Tables (PostgreSQL) - Structured data
```

## Maintenance Guarantee

**This hybrid approach is maintained going forward:**

1. **All extraction functions** write to both:
   - `extract_from_pdf_bytes()` writes JSON artefact AND relational tables
   - `map_fields()` results stored in both formats

2. **All validation functions** write to both:
   - `validate_extraction()` writes JSON artefact AND ValidationCheck records

3. **All LLM functions** write to both:
   - LLM responses stored as JSON artefact
   - Resolved fields stored in Submission metadata (relational)

4. **Backward compatibility:**
   - Functions still return dict format (for existing code)
   - Helper functions convert relational → dict when needed
   - Existing code using JSON artefacts continues to work

## When to Use Which

### Use JSON Artefacts For:
- Debugging extraction/validation issues
- Exporting complete data for analysis
- Audit trail and compliance
- Full document review
- Re-processing with different rules

### Use Relational Tables For:
- Querying fields across submissions
- Finding evidence for specific fields
- Reporting and analytics
- Building UI dashboards
- Cross-document analysis

## Migration

The migration script (`scripts/migrate_to_relational_tables.py`) populates relational tables from existing JSON artefacts, ensuring historical data is available in both formats.

## Future Considerations

- **No breaking changes:** Both storage methods will continue to be maintained
- **Optional writes:** Can disable relational writes with `write_to_tables=False` if needed
- **Performance:** JSON writes are fast (blob upload), relational writes are transactional
- **Storage costs:** JSON in blob storage, relational in database (both necessary)

