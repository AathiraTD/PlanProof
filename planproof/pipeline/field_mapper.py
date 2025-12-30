"""
Deterministic field extraction from extracted layout.
"""
from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple, Optional

POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2})\b", re.I)
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"\b(\+?\d[\d\s().-]{8,}\d)\b")
# Application ref patterns: PP-\d{6,} or 20\d{6,}[A-Z]{1,3}
APPREF_RE = re.compile(r"\b(PP-\d{6,}|20\d{6,}[A-Z]{1,3})\b", re.I)
DATE_LIKE = re.compile(r"\b\d{1,2}[./-]\d{1,2}[./-]\d{2,4}\b")

# Strong heuristics for plan sheets
ADDRESS_LIKE = re.compile(r"^\s*\d+\s+[A-Z0-9'’\- ]{4,}$")
PROPOSAL_HINTS = re.compile(r"\b(PROPOS|DEVELOPMENT|CONVERSION|USE|HMO|EXTENSION|LOFT|DORMER)\b", re.I)

LABEL_PATTERNS = {
    "site_address": [r"site address", r"address of site", r"site location"],
    "proposal_description": [r"proposal", r"description of development", r"proposed development", r"what are you proposing"],
    "applicant_name": [r"applicant name", r"name of applicant", r"first name", r"surname"],
    "agent_name": [r"agent name", r"name of agent"],
    "proposed_use": [r"i/we hereby apply for prior approval", r"prior approval for", r"declaration"],
}

DOC_TYPE_HINTS = {
    "application_form": [
        r"application form", 
        r"planning application", 
        r"town and country planning",
        r"planning portal reference",  # Doc 82: "Planning Portal Reference:"
        r"application to determine if prior approval",  # Prior Approval forms
        r"i/we hereby apply for prior approval",  # Prior Approval declaration
        r"prior approval"
    ],
    "site_notice": [
        r"statement of display of a site notice",
        r"site notice of application",
        r"site notice",
        r"notice of application"
    ],
    "site_plan": [
        r"location\s*&\s*block\s*plan", 
        r"location plan", 
        r"block plan", 
        r"\b1:1250\b", 
        r"\b1:500\b", 
        r"\b1:2500\b"
    ],
    "drawing": [r"existing", r"proposed", r"elevation", r"floor plan", r"section"],
    "design_statement": [r"design and access statement", r"design\s*&\s*access"],
    "heritage": [r"heritage statement", r"listed building", r"conservation area"],
}


def _norm(s: str) -> str:
    """Normalize whitespace."""
    return re.sub(r"\s+", " ", (s or "")).strip()


def _add_ev(ev: Dict[str, List[Dict[str, Any]]], field: str, page: int, block_id: str, snippet: str, 
            confidence: float = 0.5, source_doc_type: Optional[str] = None):
    """Add evidence entry for a field with confidence and source."""
    ev.setdefault(field, []).append({
        "page": page, 
        "block_id": block_id, 
        "snippet": _norm(snippet)[:240],
        "confidence": confidence,
        "source_doc_type": source_doc_type
    })


def _looks_like_allcaps(s: str) -> bool:
    """Check if string is mostly uppercase."""
    letters = [c for c in s if c.isalpha()]
    if len(letters) < 8:
        return False
    upp = sum(1 for c in letters if c.isupper())
    return upp / max(1, len(letters)) > 0.8


def _is_noise(s: str) -> bool:
    """Check if text block is noise (copyright, notes, etc.)."""
    sl = s.lower()
    return any(k in sl for k in ["copyright", "notes:", "scale", "printed on", "os 1000", 
                                  "disclaimer", "this drawing", "for information only"])

def _is_council_contact(s: str) -> bool:
    """Check if text contains council contact information (not applicant)."""
    sl = s.lower()
    council_indicators = [
        "birmingham.gov.uk", "planning.registration", "council", "local authority",
        "planning department", "planning@", "0121 464", "po box"
    ]
    return any(indicator in sl for indicator in council_indicators)

def _is_in_site_location_section(blocks: List[Dict[str, Any]], block_index: int) -> bool:
    """Check if block is in a 'Site Location' section (higher confidence)."""
    # Look backwards for section headers
    for i in range(max(0, block_index - 10), block_index):
        t = _norm(blocks[i].get("content", blocks[i].get("text", ""))).lower()
        if any(header in t for header in ["site location", "site address", "address of site", 
                                           "location of site", "property address"]):
            return True
    return False


def looks_like_phone(s: str) -> bool:
    """Check if string looks like a phone number (not a date)."""
    return not DATE_LIKE.search(s)


def extract_site_address_from_section(blocks: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
    """
    Extract site address from structured "Site location" section.
    Looks for Property Name, Address Line 1, Address Line 2, Town/City, Postcode fields.
    """
    address_parts = []
    start_idx = None
    
    # Find "Site location" or "Site address" section header
    for i, b in enumerate(blocks[:200]):
        t = _norm(b.get("content", b.get("text", ""))).lower()
        if any(header in t for header in ["site location", "site address", "address of site", "property address"]):
            start_idx = i
            break
    
    if start_idx is None:
        return None, None, 0.0
    
    # Collect address components from next 10-15 blocks after header
    property_name = None
    address_line1 = None
    address_line2 = None
    town_city = None
    postcode = None
    
    for i in range(start_idx + 1, min(start_idx + 20, len(blocks))):
        b = blocks[i]
        t = _norm(b.get("content", b.get("text", "")))
        tl = t.lower()
        
        # Skip empty or noise
        if not t or _is_noise(t) or len(t) < 2:
            continue
        
        # Property Name
        if "property name" in tl and not property_name:
            parts = re.split(r":", t, maxsplit=1)
            if len(parts) == 2:
                property_name = _norm(parts[1])
        
        # Address Line 1
        if "address line 1" in tl or ("address" in tl and "line" in tl and "1" in tl):
            parts = re.split(r":", t, maxsplit=1)
            if len(parts) == 2:
                address_line1 = _norm(parts[1])
        
        # Address Line 2
        if "address line 2" in tl or ("address" in tl and "line" in tl and "2" in tl):
            parts = re.split(r":", t, maxsplit=1)
            if len(parts) == 2:
                address_line2 = _norm(parts[1])
        
        # Town/City
        if "town" in tl or "city" in tl:
            parts = re.split(r":", t, maxsplit=1)
            if len(parts) == 2:
                town_city = _norm(parts[1])
        
        # Postcode
        if "postcode" in tl:
            parts = re.split(r":", t, maxsplit=1)
            if len(parts) == 2:
                postcode_match = POSTCODE_RE.search(parts[1])
                if postcode_match:
                    postcode = postcode_match.group(1).upper()
        
        # Also try to extract values without labels (next block after label)
        if i > start_idx + 1:
            prev_t = _norm(blocks[i-1].get("content", blocks[i-1].get("text", ""))).lower()
            if "property name" in prev_t and not property_name:
                property_name = t
            elif ("address line 1" in prev_t or "address" in prev_t) and not address_line1:
                address_line1 = t
            elif "address line 2" in prev_t and not address_line2:
                address_line2 = t
            elif ("town" in prev_t or "city" in prev_t) and not town_city:
                town_city = t
            elif "postcode" in prev_t and not postcode:
                postcode_match = POSTCODE_RE.search(t)
                if postcode_match:
                    postcode = postcode_match.group(1).upper()
    
    # Build full address string
    address_parts = []
    if property_name:
        address_parts.append(property_name)
    if address_line1:
        address_parts.append(address_line1)
    if address_line2:
        address_parts.append(address_line2)
    if town_city:
        address_parts.append(town_city)
    if postcode:
        address_parts.append(postcode)
    
    if address_parts:
        full_address = ", ".join(address_parts)
        # Use the block containing the section header as source
        source_block = blocks[start_idx] if start_idx < len(blocks) else blocks[0]
        return full_address, source_block, 0.95  # High confidence for structured extraction
    
    return None, None, 0.0


def extract_address_from_demolition_pattern(blocks: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
    """
    Extract site address from "demolition of ..." pattern (for site notices).
    Pattern: "demolition of Unit M, Dorset Road, Saltley Business Park, Saltley, Birmingham, B8 1BG"
    """
    for i, b in enumerate(blocks[:100]):
        t = _norm(b.get("content", b.get("text", "")))
        tl = t.lower()
        
        if "demolition of" in tl or "demolition" in tl:
            # Try to extract from "demolition of" to first postcode
            match = re.search(r"demolition\s+of\s+(.+?)(?:\s+([A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}))", t, re.I)
            if match:
                address_part = match.group(1).strip()
                postcode_part = match.group(2).upper() if match.lastindex >= 2 else None
                
                # Clean up address (remove trailing commas, normalize)
                address_part = re.sub(r",\s*$", "", address_part)
                if postcode_part:
                    full_address = f"{address_part}, {postcode_part}"
                else:
                    full_address = address_part
                
                if len(full_address) > 10:  # Must be substantial
                    return full_address, b, 0.85
    
    return None, None, 0.0


def pick_site_address(blocks: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
    """
    Pick site address with multiple strategies:
    1. Structured extraction from "Site location" section (highest confidence)
    2. Pattern extraction from "demolition of" text (for site notices)
    3. Heuristic extraction from plan sheets (lowest confidence, filtered for noise)
    """
    # Strategy 1: Structured extraction from Site Location section (best for application forms)
    addr, block, conf = extract_site_address_from_section(blocks)
    if addr and conf >= 0.9:
        return addr, block, conf
    
    # Strategy 2: Extract from "demolition of" pattern (for site notices)
    addr, block, conf = extract_address_from_demolition_pattern(blocks)
    if addr and conf >= 0.8:
        return addr, block, conf
    
    # Strategy 3: Heuristic extraction (for plan sheets, but filter noise carefully)
    best_match = None
    best_block = None
    best_confidence = 0.0
    
    for i, b in enumerate(blocks[:100]):
        t = _norm(b.get("content", b.get("text", "")))
        if not t or _is_noise(t):
            continue
        
        # Skip if it's a disclaimer or too short
        if len(t) < 5 or "disclaimer" in t.lower() or "for information" in t.lower():
            continue
        
        # Skip if it looks like a map grid reference (just numbers like "4 2447")
        if re.match(r"^\s*\d+\s+\d+\s*$", t):
            continue
        
        # Skip if it's just numbers (grid coordinates)
        if re.match(r"^\s*\d+\s*$", t):
            continue
        
        # Check if it's in Site Location section (high confidence)
        in_site_section = _is_in_site_location_section(blocks, i)
        
        # Check if it matches address pattern
        if ADDRESS_LIKE.match(t):
            confidence = 0.7 if in_site_section else 0.4
            if confidence > best_confidence:
                best_match = t
                best_block = b
                best_confidence = confidence
        # Also try labeled extraction
        elif any(label in t.lower() for label in ["site address", "address of site", "site location"]):
            # Try to extract value after colon
            parts = re.split(r":", t, maxsplit=1)
            if len(parts) == 2 and _norm(parts[1]):
                val = _norm(parts[1])
                if len(val) > 5:  # Must be substantial
                    confidence = 0.8 if in_site_section else 0.6
                    if confidence > best_confidence:
                        best_match = val
                        best_block = b
                        best_confidence = confidence
    
    if best_match and best_confidence > 0.3:
        return best_match, best_block, best_confidence
    
    return None, None, 0.0


def pick_proposed_use(blocks: List[Dict[str, Any]]) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
    """Pick proposed use from plan sheet (all caps sentence with proposal keywords)."""
    for b in blocks[:80]:
        t = _norm(b.get("content", b.get("text", "")))
        if not t or _is_noise(t):
            continue
        if PROPOSAL_HINTS.search(t) and (len(t) >= 20) and (_looks_like_allcaps(t) or t.endswith(".")):
            confidence = 0.7 if len(t) >= 30 else 0.5
            return t, b, confidence
    return None, None, 0.0


def classify_document(text_blocks: List[Dict[str, Any]]) -> str:
    """Classify document type from text content."""
    text = " ".join(_norm(b.get("content", b.get("text", ""))) for b in text_blocks[:200]).lower()
    
    # Priority order: check more specific types first
    # application_form and site_notice should be checked before generic types
    priority_order = ["application_form", "site_notice", "site_plan", "design_statement", "heritage", "drawing"]
    
    best = ("unknown", 0)
    for dtype in priority_order:
        if dtype not in DOC_TYPE_HINTS:
            continue
        hints = DOC_TYPE_HINTS[dtype]
        score = sum(1 for h in hints if re.search(h, text))
        if score > best[1]:
            best = (dtype, score)
    
    # If no match found, check remaining types
    if best[1] == 0:
        for dtype, hints in DOC_TYPE_HINTS.items():
            if dtype not in priority_order:
                score = sum(1 for h in hints if re.search(h, text))
                if score > best[1]:
                    best = (dtype, score)
    
    return best[0]


def extract_by_label(text_blocks: List[Dict[str, Any]], label_patterns: List[str]) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Extract field value by looking for label patterns."""
    # look for label in a block, then take same block after ":" or next 1–2 blocks
    for i, b in enumerate(text_blocks):
        t = _norm(b.get("content", b.get("text", "")))
        tl = t.lower()
        if any(re.search(p, tl) for p in label_patterns):
            # try "Label: value"
            m = re.split(r":", t, maxsplit=1)
            if len(m) == 2 and _norm(m[1]):
                return _norm(m[1]), b
            # else take next blocks
            nxt = []
            for j in range(1, 4):
                if i + j < len(text_blocks):
                    nxt_txt = _norm(text_blocks[i+j].get("content", text_blocks[i+j].get("text", "")))
                    if nxt_txt:
                        nxt.append(nxt_txt)
                if len(" ".join(nxt)) > 20:
                    break
            if nxt:
                return _norm(" ".join(nxt)), b
    return None, None


def map_fields(extracted_layout: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract structured fields from extracted layout.
    
    Returns:
        {
            "fields": {field_name: value, ...},
            "evidence_index": {field_name: [{"page": int, "block_id": str, "snippet": str}, ...]}
        }
    """
    blocks = extracted_layout.get("text_blocks", []) or []
    fields: Dict[str, Any] = {}
    evidence: Dict[str, List[Dict[str, Any]]] = {}

    # document type
    dtype = classify_document(blocks)
    fields["document_type"] = dtype

    # app ref - try PP-\d+ pattern first (more common), then year-based pattern
    # Pattern: \bPP-\d{6,}\b (e.g., PP-14469287)
    for b in blocks[:400]:
        t = b.get("content", b.get("text", ""))
        m = APPREF_RE.search(t)
        if m:
            ref = m.group(1).upper()
            # Normalize PP-14469287 format
            if ref.startswith("PP-"):
                fields["application_ref"] = ref
            else:
                fields["application_ref"] = ref
            fields["application_ref_confidence"] = 0.9 if "PP-" in ref else 0.8
            page_num = int(b.get("page_number", b.get("page", 0)))
            block_id = f"p{page_num}b{b.get('index', '')}"
            confidence = 0.9 if "PP-" in ref else 0.8
            _add_ev(evidence, "application_ref", page_num, block_id, t, confidence, dtype)
            break

    # site_address - use improved heuristic
    if "site_address" not in fields:
        addr, src, conf = pick_site_address(blocks)
        if addr:
            fields["site_address"] = addr
            fields["site_address_confidence"] = conf
            page_num = int(src.get("page_number", src.get("page", 0)))
            block_id = f"p{page_num}b{src.get('index', '')}"
            _add_ev(evidence, "site_address", page_num, block_id, src.get("content", src.get("text", "")), conf, dtype)
    
    # proposed_use - try Prior Approval pattern first, then heuristic
    if "proposed_use" not in fields:
        # Try to extract from "I/We hereby apply for Prior Approval:" pattern
        for i, b in enumerate(blocks[:100]):
            t = _norm(b.get("content", b.get("text", "")))
            tl = t.lower()
            if "i/we hereby apply for prior approval" in tl or "prior approval for" in tl:
                # Extract the description after the colon or "for"
                parts = re.split(r":|for", t, maxsplit=1)
                if len(parts) == 2:
                    prop_text = _norm(parts[1])
                    if len(prop_text) > 10:
                        fields["proposed_use"] = prop_text
                        fields["proposed_use_confidence"] = 0.9
                        page_num = int(b.get("page_number", b.get("page", 0)))
                        block_id = f"p{page_num}b{b.get('index', '')}"
                        _add_ev(evidence, "proposed_use", page_num, block_id, t, 0.9, dtype)
                        break
        
        # Fallback to heuristic extraction
        if "proposed_use" not in fields:
            prop, src, conf = pick_proposed_use(blocks)
            if prop:
                fields["proposed_use"] = prop
                fields["proposed_use_confidence"] = conf
                page_num = int(src.get("page_number", src.get("page", 0)))
                block_id = f"p{page_num}b{src.get('index', '')}"
                _add_ev(evidence, "proposed_use", page_num, block_id, src.get("content", src.get("text", "")), conf, dtype)

    # labeled fields (fallback for other fields)
    for field, pats in LABEL_PATTERNS.items():
        if field not in fields:  # Skip if already found
            val, src = extract_by_label(blocks, pats)
            if val:
                fields[field] = val
                fields[f"{field}_confidence"] = 0.7  # Label-based extraction is medium confidence
                page_num = int(src.get("page_number", src.get("page", 0)))
                block_id = f"p{page_num}b{src.get('index', '')}"
                _add_ev(evidence, field, page_num, block_id, src.get("content", src.get("text", "")), 0.7, dtype)

    # regex fields (email/phone/postcode) - exclude council contact info
    site_location_blocks = []  # Track blocks in Site Location section
    for i, b in enumerate(blocks[:400]):
        t = b.get("content", b.get("text", ""))
        if _is_in_site_location_section(blocks, i):
            site_location_blocks.append((i, b, t))
    
    # Postcode extraction with context ranking
    # Strategy: Prefer postcodes near "Site location" or "Postcode" label
    # Hard-deprioritize PO Box postcodes (B1 1TU) when near council contact info
    postcode_candidates = []
    
    # First: Collect all postcodes with context scoring
    for i, b in enumerate(blocks[:400]):
        t = b.get("content", b.get("text", ""))
        m = POSTCODE_RE.search(t)
        if m:
            postcode = m.group(1).upper()
            confidence = 0.5  # Base confidence
            
            # Check context for ranking
            in_site_section = _is_in_site_location_section(blocks, i)
            tl = t.lower()
            
            # High confidence: In Site Location section or near "Postcode" label
            if in_site_section or "postcode" in tl:
                confidence = 0.9
            # Medium confidence: Near "Site" or "Address" keywords
            elif "site" in tl or "address" in tl:
                confidence = 0.7
            # Low confidence: Default
            else:
                confidence = 0.5
            
            # Hard-deprioritize PO Box postcodes (B1 1TU, etc.) when near council contact info
            if _is_council_contact(t) or "po box" in tl or "birmingham city council" in tl:
                # Reduce confidence significantly for council PO box postcodes
                if postcode.startswith("B1 1TU") or "po box" in tl:
                    confidence = 0.1  # Very low - likely council PO box, not site postcode
            
            postcode_candidates.append((postcode, b, confidence, i))
    
    # If we have candidates, use the highest confidence one
    if postcode_candidates and "postcode" not in fields:
        # Sort by confidence (highest first)
        postcode_candidates.sort(key=lambda x: x[2], reverse=True)
        postcode, b, conf, idx = postcode_candidates[0]
        
        # Only use if confidence is reasonable (avoid council PO boxes)
        if conf >= 0.3:
            fields["postcode"] = postcode
            fields["postcode_confidence"] = conf
            page_num = int(b.get("page_number", b.get("page", 0)))
            block_id = f"p{page_num}b{b.get('index', '')}"
            _add_ev(evidence, "postcode", page_num, block_id, b.get("content", b.get("text", "")), conf, dtype)
    
    # Applicant email/phone - exclude council contact info
    for i, b in enumerate(blocks[:400]):
        t = b.get("content", b.get("text", ""))
        
        # Skip council contact blocks
        if _is_council_contact(t):
            continue
        
        if "applicant_email" not in fields:
            m = EMAIL_RE.search(t)
            if m:
                # Additional check: prefer emails near "applicant" context
                context_blocks = blocks[max(0, i-2):min(len(blocks), i+3)]
                context = " ".join([_norm(cb.get("content", cb.get("text", ""))) for cb in context_blocks]).lower()
                confidence = 0.8 if "applicant" in context else 0.5
                fields["applicant_email"] = m.group(0)
                fields["applicant_email_confidence"] = confidence
                page_num = int(b.get("page_number", b.get("page", 0)))
                block_id = f"p{page_num}b{b.get('index', '')}"
                _add_ev(evidence, "applicant_email", page_num, block_id, t, confidence, dtype)
        
        if "applicant_phone" not in fields:
            m = PHONE_RE.search(t)
            if m and looks_like_phone(m.group(1)) and len(_norm(m.group(1))) >= 9:
                # Additional check: prefer phones near "applicant" context
                context_blocks = blocks[max(0, i-2):min(len(blocks), i+3)]
                context = " ".join([_norm(cb.get("content", cb.get("text", ""))) for cb in context_blocks]).lower()
                confidence = 0.8 if "applicant" in context else 0.5
                fields["applicant_phone"] = _norm(m.group(1))
                fields["applicant_phone_confidence"] = confidence
                page_num = int(b.get("page_number", b.get("page", 0)))
                block_id = f"p{page_num}b{b.get('index', '')}"
                _add_ev(evidence, "applicant_phone", page_num, block_id, t, confidence, dtype)


    return {"fields": fields, "evidence_index": evidence}

