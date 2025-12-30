# Ground Truth Fixes - Implementation Summary

## Overview

All fixes identified from the ground-truth comparative study have been implemented. This document summarizes what was fixed and how.

## Fixes Implemented

### ✅ Fix 1: Document Classification Improvements

**Problem:** 
- Doc 82 (application form) classified as "drawing"
- Doc 83 (site notice) classified as "application_form"

**Solution:**
- Added detection patterns for `application_form`:
  - "Planning Portal Reference:"
  - "Application to determine if prior approval"
  - "I/We hereby apply for Prior Approval"
  - "Prior Approval"
- Added new `site_notice` document type with patterns:
  - "Statement of Display of a Site Notice"
  - "Site Notice of Application"
  - "Site Notice"
- Implemented priority-based classification (checks specific types first)

**Location:** `planproof/pipeline/field_mapper.py` lines 26-51

---

### ✅ Fix 2: Application Reference Extraction

**Problem:** PP-14469287 not extracted, causing R3 "needs_review" + LLM trigger

**Solution:**
- Regex pattern already includes `PP-\d{6,}` (was correct)
- Added confidence scoring (0.9 for PP- format)
- Ensured pattern searches across all text blocks

**Location:** `planproof/pipeline/field_mapper.py` lines 397-414

---

### ✅ Fix 3: Site Address Extraction - Structured Section

**Problem:** 
- Doc 82: Extracted disclaimer instead of Site Location section
- Doc 83: Didn't extract address from "demolition of" pattern
- Doc 81: Extracted noise ("4 2447" grid labels)

**Solution:**
- **New function:** `extract_site_address_from_section()` - Extracts from structured "Site location" section
  - Looks for Property Name, Address Line 1, Address Line 2, Town/City, Postcode fields
  - Builds full address: "Property Name, Address Line 1, Address Line 2, Town/City, Postcode"
  - Confidence: 0.95 (very high for structured extraction)
  
- **New function:** `extract_address_from_demolition_pattern()` - Extracts from "demolition of ..." pattern
  - Pattern: "demolition of Unit M, Dorset Road, Saltley Business Park, Saltley, Birmingham, B8 1BG"
  - Confidence: 0.85
  
- **Enhanced `pick_site_address()`:** 
  - Strategy 1: Structured extraction (highest priority)
  - Strategy 2: Demolition pattern (for site notices)
  - Strategy 3: Heuristic (for plan sheets, with noise filtering)
  - Filters out grid references like "4 2447" (just numbers)
  - Filters out disclaimers

**Location:** `planproof/pipeline/field_mapper.py` lines 105-250

---

### ✅ Fix 4: Postcode Extraction with Context Ranking

**Problem:** 
- Doc 82: Extracted B1 1TU (council PO box) instead of B8 1BG (site postcode)
- No context awareness

**Solution:**
- **Context-based ranking:**
  - High confidence (0.9): In Site Location section or near "Postcode" label
  - Medium confidence (0.7): Near "Site" or "Address" keywords
  - Low confidence (0.5): Default
  - Very low confidence (0.1): PO Box postcodes near council contact info
  
- **Hard-deprioritize PO Box postcodes:**
  - Detects "PO Box", "Birmingham City Council", council contact blocks
  - Reduces confidence to 0.1 for B1 1TU when near council info
  - Only uses postcode if confidence >= 0.3 (filters out council PO boxes)

**Location:** `planproof/pipeline/field_mapper.py` lines 448-480

---

### ✅ Fix 5: Proposed Use Extraction

**Problem:** Missing from Doc 82; should extract from "I/We hereby apply for Prior Approval:" pattern

**Solution:**
- **Pattern extraction:** Extracts from "I/We hereby apply for Prior Approval:" or "Prior Approval for" patterns
- Extracts description after colon or "for"
- Confidence: 0.9 (high for pattern-based extraction)
- Fallback to heuristic extraction if pattern not found

**Location:** `planproof/pipeline/field_mapper.py` lines 427-450

---

### ✅ Fix 6: Applicant Name Extraction

**Problem:** Not extracted at all from Doc 82

**Solution:**
- **Structured extraction:** Extracts from "First name" and "Surname" labels
- Builds name: "First Name Surname (Company Name)" if company present
- Checks both labeled extraction (after colon) and next block
- Confidence: 0.8

**Location:** `planproof/pipeline/field_mapper.py` lines 437-480

---

### ✅ Fix 7: Applicant Contact Extraction - Negative Filters

**Problem:** 
- Extracted council email (planning.registration@birmingham.gov.uk)
- Extracted council phone (0121 464 3669)

**Solution:**
- **Enhanced `_is_council_contact()`:** Detects council contact info
  - birmingham.gov.uk
  - planning.registration
  - council, local authority
  - planning department
  - 0121 464 (Birmingham council phone prefix)
  - PO Box
  
- **Context-aware extraction:** Prefers emails/phones near "applicant" keyword
  - Confidence: 0.8 if near "applicant", 0.5 otherwise
  - Skips blocks containing council contact indicators

**Location:** `planproof/pipeline/field_mapper.py` lines 88-95, 482-514

---

### ✅ Fix 8: Doc-Type-Aware Required Fields

**Problem:** Rules treating all documents as if they must satisfy global required fields

**Solution:**
- **Updated rule catalog:** Added `applies_to` field (already done)
- **Updated field ownership:** Added `site_notice` to `DOC_FIELD_OWNERSHIP`
  - `application_form`: All fields (application_ref, site_address, postcode, proposed_use, applicant_name, etc.)
  - `site_notice`: site_address, postcode, proposed_use (supporting evidence)
  - `site_plan`: site_address, postcode (optional)
  
- **Validation logic:** Already skips rules that don't apply to document type

**Location:** 
- `artefacts/rule_catalog.json` - Updated applies_to fields
- `planproof/pipeline/llm_gate.py` - Updated DOC_FIELD_OWNERSHIP

---

## Expected Improvements

### Document 82 (Application Form)
- ✅ Should classify as `application_form` (not "drawing")
- ✅ Should extract `application_ref`: PP-14469287
- ✅ Should extract `site_address`: "Saltley Business Park, Unit M, Dorset Road, Washwood Heath, Birmingham, B8 1BG"
- ✅ Should extract `postcode`: B8 1BG (not B1 1TU)
- ✅ Should extract `proposed_use`: From Prior Approval declaration
- ✅ Should extract `applicant_name`: "Daniel Green (High Speed Two (HS2) Limited)"
- ✅ Should NOT extract council contact as applicant contact

### Document 83 (Site Notice)
- ✅ Should classify as `site_notice` (not "application_form")
- ✅ Should extract `site_address`: From "demolition of" pattern
- ✅ Should extract `postcode`: B8 1BG (with context ranking)
- ✅ Should NOT require `application_ref` (not applicable to site notices)

### Document 81 (Site Plan)
- ✅ Should classify as `site_plan` (already correct)
- ✅ Should NOT extract noise like "4 2447" as address
- ✅ Should NOT require `application_ref` or `proposed_use` (not applicable to site plans)

---

## Testing Checklist

- [ ] Test Doc 82 classification → should be "application_form"
- [ ] Test Doc 82 application_ref → should extract "PP-14469287"
- [ ] Test Doc 82 site_address → should extract structured address (not disclaimer)
- [ ] Test Doc 82 postcode → should extract B8 1BG (not B1 1TU)
- [ ] Test Doc 82 proposed_use → should extract from Prior Approval pattern
- [ ] Test Doc 82 applicant_name → should extract "Daniel Green (HS2)"
- [ ] Test Doc 82 applicant contact → should NOT extract council contacts
- [ ] Test Doc 83 classification → should be "site_notice"
- [ ] Test Doc 83 site_address → should extract from "demolition of" pattern
- [ ] Test Doc 83 validation → should NOT require application_ref
- [ ] Test Doc 81 site_address → should NOT extract "4 2447"
- [ ] Test Doc 81 validation → should NOT require application_ref or proposed_use

---

## Files Modified

1. `planproof/pipeline/field_mapper.py` - All extraction improvements
2. `artefacts/rule_catalog.json` - Added site_notice to applies_to
3. `planproof/pipeline/llm_gate.py` - Updated DOC_FIELD_OWNERSHIP

---

## Next Steps

1. Run tests with the 3 documents to verify improvements
2. Monitor extraction accuracy and LLM trigger rate
3. Adjust confidence thresholds if needed
4. Add more patterns based on real-world results

