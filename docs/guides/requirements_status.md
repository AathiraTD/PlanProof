# PlanProof MVP Requirements Status

## Requirements We Have Implemented

1. Document ingestion with Azure Blob Storage upload and content hash deduplication
2. Document extraction using Azure Document Intelligence with tiered OCR approach (prebuilt-layout model)
3. Document classification into types (application_form, site_plan, drawing, design_statement, heritage, unknown)
4. Evidence-backed field extraction with page numbers, bounding boxes, and snippets linked to extracted values
5. Field extraction using deterministic methods (regex patterns, heuristics, label matching)
6. Database schema with all required tables (PlanningCase/Application, Submission, Document, Page, Evidence, ExtractedField, GeometryFeature, SpatialMetric, ChangeSet, ChangeItem, Rule, ValidationCheck)
7. Hybrid storage strategy (JSON artefacts in blob storage plus relational tables in database)
8. Rule catalog system that parses validation rules from markdown and stores as JSON
9. Deterministic validation engine that checks required fields against rules
10. Validation results with PASS, FAIL, NEEDS_REVIEW statuses and evidence pointers
11. Gated LLM assistance that only triggers when confidence thresholds are met and fields are missing
12. LLM field resolution with structured JSON output and evidence citations
13. Application-level and submission-level caching of resolved fields to avoid redundant LLM calls
14. Run tracking and audit trail for processing operations
15. Batch processing of multiple PDFs in a folder for a single application
16. End-to-end pipeline from ingestion through extraction, validation, and optional LLM resolution
17. PostGIS database support with geometry columns defined (though not actively used yet)
18. Submission versioning system (V0, V1+) with parent-child relationships for modifications
19. Content hash-based document deduplication
20. Artefact storage in blob storage for complete audit trail

## Requirements Yet to Implement

1. Human-in-the-loop UI (Streamlit interface) for officer review and override
2. Document viewer with page thumbnails, zoom, and search functionality
3. Evidence navigation UI that allows jumping to evidence bounding boxes from validation failures
4. Officer override functionality with notes and audit trail
5. Export functionality to generate validation report as JSON or PDF
6. Delta computation engine to compare V0 vs V1+ submissions and generate ChangeSets
7. ChangeItem generation for field deltas, document deltas, and spatial metric deltas
8. Significance scoring for changes to determine which rules need revalidation
9. Modification workflow that links V1+ submissions to parent V0 and computes deltas
10. Spatial geometry feature creation (manual or assisted outline input for site boundaries, extensions, balconies)
11. Spatial metric computation (min distance to boundary, area, projection depth calculations)
12. Spatial validation rules that execute when geometry and metrics exist
13. Document type-specific required document validation (DOCUMENT_REQUIRED rule category)
14. Consistency validation rules that check field matches across multiple documents
15. Modification validation rules that verify parent case references and delta completeness
16. Tiered OCR fallback (Tier 2: Azure Document Intelligence, Tier 3: Tesseract OCR) - currently only Tier 1 and Tier 2 implemented
17. Conflict detection and reconciliation when multiple sources provide different values for the same field
18. RBAC (Role-Based Access Control) for different user roles (Validation Officer, Team Lead, Governance)
19. Dashboard for team leads showing consistency metrics and throughput
20. Search functionality using PostgreSQL full-text search or Azure AI Search
21. Officer decision logging with timestamps and rationale
22. Request-info workflow for submissions that need more information
23. Case and submission overview screen showing metadata, version history, and status
24. Extracted fields viewer with filtering by confidence level
25. Validation results viewer with drilldown to supporting evidence
26. Delta view for modifications showing ChangeSet summary and impacted rules
27. Comparison view for V0 vs V1+ submissions side-by-side
28. Rule configuration UI or mechanism to update rules without code redeploy
29. Monitoring and observability dashboards (Application Insights integration)
30. Security features (encryption at rest and in transit, least privilege access)
31. Data retention controls and policy enforcement
32. Golden-case test set for verification
33. Evidence integrity checks to ensure every failure has evidence pointers
34. Usability walkthrough testing for officer workflows

## Gaps in Existing Implementation

1. ChangeSet and ChangeItem database tables exist but no code computes or populates them
2. GeometryFeature and SpatialMetric tables exist but no code creates or uses them
3. Document type classification exists but not all required document types are fully supported (Location Plan, Site Plan, Existing Floor Plans, Proposed Floor Plans, Existing Elevations, Proposed Elevations, Design & Access Statement, Other Supporting Document)
4. Field extraction covers basic fields but may not cover all fields in the Field Dictionary
5. Validation rules are loaded from catalog but only DOCUMENT_REQUIRED category is partially implemented; CONSISTENCY, MODIFICATION, and SPATIAL categories are not implemented
6. Evidence pointers exist but UI to navigate from validation failure to evidence location is missing
7. LLM gating logic exists but may need refinement for edge cases and confidence thresholds
8. Submission metadata storage exists but modification workflow that uses it is not implemented
9. PostGIS extension support is configured but no spatial queries or geometry operations are implemented
10. Rule catalog supports JSON/YAML but no mechanism to update rules without rebuilding catalog file
11. Export functionality mentioned in requirements but no code generates reports
12. Audit trail exists in database but no UI to view or search audit logs
13. Conflict detection logic mentioned but not fully implemented for field value conflicts
14. Tiered OCR approach documented but Tesseract fallback (Tier 3) is not implemented
15. Field Dictionary canonical list exists implicitly but not as a formal configurable dictionary
16. Officer override functionality is mentioned in requirements but no database fields or code support it
17. Request-info workflow is mentioned but no status tracking or workflow implementation exists
18. Significance scoring for changes is mentioned but no algorithm or code exists
19. Impacted rule identification from deltas is mentioned but not implemented
20. Revalidation targeting based on delta significance is mentioned but not implemented

