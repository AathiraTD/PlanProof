# Extraction Quality Fixes - Implementation Summary

## Overview

This document summarizes all fixes implemented to address the mentor's feedback on extraction quality, completeness, efficiency, and coherence.

## Fixes Implemented

### ✅ Fix 1: Deterministic Extractors for "Easy Wins"

**Problem:** Missing deterministic extractors for common patterns, causing unnecessary LLM triggers.

**Solution:**
- **Application Ref:** Added `PP-\d{6,}` pattern to regex (e.g., "PP-14469287")
  - Location: `planproof/pipeline/field_mapper.py` line 11
  - Pattern now matches both `PP-14469287` and `20\d{6,}[A-Z]{1,3}` formats
  - Confidence: 0.9 for PP- format, 0.8 for year-based format

- **UK Postcode:** Prefer postcodes from "Site Location" section
  - Location: `planproof/pipeline/field_mapper.py` lines 253-285
  - High confidence (0.9) for postcodes in Site Location section
  - Lower confidence (0.4-0.6) for postcodes in headers/footers
  - Prevents confusion between council PO box (B1 1TU) and site postcode (B8 1BG)

- **Site Address:** Improved extraction from Site Location fields
  - Location: `planproof/pipeline/field_mapper.py` lines 64-100
  - Filters out noise (disclaimers, map grids like "4 2447")
  - Prefers addresses in "Site Location" section (confidence 0.8)
  - Supports labeled extraction ("Site Address: ...")
  - Skips short strings and disclaimer text

**Impact:** Should eliminate most LLM triggers for application forms.

---

### ✅ Fix 2: Doc-Type-Aware Required Fields

**Problem:** Site plans were being required to provide `application_ref` and `proposed_use`, causing unnecessary LLM triggers.

**Solution:**
- **Rule Catalog:** Updated `artefacts/rule_catalog.json` with `applies_to` field
  - R1 (Site Address): applies to `["application_form", "site_plan"]`
  - R2 (Proposed Use): applies to `["application_form", "design_statement"]`
  - R3 (Application Ref): applies to `["application_form"]` only

- **Validation Logic:** Added document type checking in `validate_extraction()`
  - Location: `planproof/pipeline/validate.py` lines 362-368
  - Rules are skipped if document type doesn't match `applies_to` list
  - Site plans no longer trigger LLM for missing `application_ref`/`proposed_use`

**Impact:** Site plans will only validate fields they can reasonably provide.

---

### ✅ Fix 3: Field-Level Provenance + Confidence

**Problem:** No confidence scores or source tracking, making it impossible to decide "auto-pass" vs "needs_review" vs "send to LLM".

**Solution:**
- **Confidence Scores:** Added confidence to all extracted fields
  - Location: `planproof/pipeline/field_mapper.py` throughout
  - Fields now include `{field_name}_confidence` (e.g., `site_address_confidence: 0.8`)
  - Confidence levels:
    - High (0.8-0.9): Site Location section, labeled fields, PP- format refs
    - Medium (0.6-0.7): Label-based extraction, general postcodes
    - Low (0.4-0.5): Unlabeled extraction, header/footer postcodes

- **Source Tracking:** Added `source_doc_type` to evidence
  - Location: `planproof/pipeline/field_mapper.py` `_add_ev()` function
  - Evidence entries now include:
    - `confidence`: Field confidence score
    - `source_doc_type`: Document type where field was found
    - `page`: Page number
    - `block_id`: Block identifier
    - `snippet`: Text snippet

**Impact:** Can now make informed decisions about field quality and whether LLM is needed.

---

### ✅ Fix 4: Persistence Keys

**Problem:** Missing metadata (`analyzed_at`, `document_id`, `run_id`, `submission_id`, `document_hash`) in outputs.

**Solution:**
- **Added to Extraction Output:** `planproof/pipeline/extract.py` lines 334-355
  - `document_id`: Document ID from database
  - `submission_id`: Submission ID (if available)
  - `run_id`: Run ID from context
  - `document_hash`: Content hash for deduplication
  - `analyzed_at`: ISO timestamp of extraction

- **Context Passing:** Updated `run_orchestrator.py` to pass context
  - Location: `planproof/ui/run_orchestrator.py` line 153
  - Context includes `run_id` for linking

**Impact:** All artifacts are now fully linkable and traceable.

---

### ✅ Fix 5: Exclude Council Contact Info

**Problem:** Applicant phone/email were being extracted from council contact information.

**Solution:**
- **Council Contact Detection:** Added `_is_council_contact()` function
  - Location: `planproof/pipeline/field_mapper.py` lines 60-66
  - Detects: `birmingham.gov.uk`, `planning.registration`, `council`, `local authority`, `planning department`, `0121 464`, `po box`

- **Context-Aware Extraction:** Prefer emails/phones near "applicant" context
  - Location: `planproof/pipeline/field_mapper.py` lines 287-320
  - Checks surrounding blocks for "applicant" keyword
  - Confidence: 0.8 if near "applicant", 0.5 otherwise
  - Skips blocks containing council contact indicators

**Impact:** Applicant contact info should no longer be confused with council contact details.

---

### ✅ Fix 6: Improved Site Address Extraction

**Problem:** Site address extraction was picking up noise (disclaimers, map grids like "4 2447").

**Solution:**
- **Enhanced `pick_site_address()` Function:**
  - Location: `planproof/pipeline/field_mapper.py` lines 64-100
  - Filters:
    - Skips disclaimers ("disclaimer", "for information only")
    - Skips map grid references (just numbers like "4 2447")
    - Requires minimum length (5 characters)
    - Prefers Site Location section (higher confidence)
  - Supports both pattern matching and labeled extraction

- **Noise Detection:** Enhanced `_is_noise()` function
  - Location: `planproof/pipeline/field_mapper.py` lines 53-57
  - Added: "disclaimer", "this drawing", "for information only"

**Impact:** Site addresses should be more accurate and less noisy.

---

## Expected Improvements

### Effectiveness (Accuracy)
- **Before:** 3/10 (wrong fields, council contact confusion)
- **After:** Expected 7-8/10
  - Application refs should be found (PP- pattern)
  - Site addresses should be cleaner (noise filtered)
  - Applicant contact should be correct (council excluded)
  - Postcodes should prefer Site Location (B8 1BG over B1 1TU)

### Completeness
- **Before:** 4/10 (missing fields on every doc)
- **After:** Expected 7-8/10
  - Application forms should extract all required fields deterministically
  - Site plans won't be penalized for missing application_ref/proposed_use

### Efficiency
- **Before:** 2/10 (LLM triggered for all docs)
- **After:** Expected 7-8/10
  - Deterministic extractors should handle most cases
  - Doc-type-aware rules prevent unnecessary LLM triggers
  - Site plans won't trigger LLM for fields they can't provide

### Coherence/Reviewability
- **Before:** 7/10 (good evidence indexing)
- **After:** Expected 9/10
  - Added confidence scores for decision-making
  - Added persistence keys for full traceability
  - Added source tracking (document type, page, block)

---

## Testing Recommendations

1. **Test Application Ref Extraction:**
   - Verify "PP-14469287" is extracted correctly
   - Verify confidence is 0.9 for PP- format

2. **Test Site Address Extraction:**
   - Verify "4 2447" (map grid) is NOT extracted as address
   - Verify actual addresses from Site Location section are extracted
   - Verify disclaimers are filtered out

3. **Test Postcode Extraction:**
   - Verify B8 1BG (site postcode) is preferred over B1 1TU (council PO box)
   - Verify confidence is higher for Site Location postcodes

4. **Test Applicant Contact:**
   - Verify council emails (planning.registration@birmingham.gov.uk) are excluded
   - Verify council phones (0121 464 3669) are excluded
   - Verify applicant contact is extracted when near "applicant" context

5. **Test Doc-Type-Aware Validation:**
   - Verify site_plan doesn't trigger LLM for missing application_ref
   - Verify site_plan doesn't trigger LLM for missing proposed_use
   - Verify application_form still validates all required fields

6. **Test Confidence Scores:**
   - Verify all extracted fields have confidence scores
   - Verify confidence is higher for Site Location fields
   - Verify confidence is lower for header/footer fields

7. **Test Persistence Keys:**
   - Verify extraction outputs include document_id, run_id, submission_id
   - Verify analyzed_at timestamp is present
   - Verify document_hash is included (if available)

---

## Files Modified

1. `planproof/pipeline/field_mapper.py` - Enhanced extraction logic
2. `artefacts/rule_catalog.json` - Added `applies_to` field to rules
3. `planproof/pipeline/validate.py` - Added document type checking
4. `planproof/pipeline/extract.py` - Added persistence keys
5. `planproof/ui/run_orchestrator.py` - Pass context for persistence keys

---

## Next Steps

1. Run tests with the three documents from run 10
2. Verify extraction quality improvements
3. Monitor LLM trigger rate (should decrease significantly)
4. Review confidence scores and adjust thresholds if needed
5. Consider adding more deterministic extractors based on results

