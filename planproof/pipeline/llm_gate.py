"""
LLM Gate module: Use Azure OpenAI to resolve validation issues when deterministic rules fail.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from planproof.aoai import AzureOpenAIClient
from planproof.db import Database, Document, ValidationResult, ValidationStatus
from planproof.pipeline.extract import get_extraction_result
from planproof.docintel import DocumentIntelligence


def resolve_with_llm(
    document_id: int,
    field_name: Optional[str] = None,
    min_confidence_threshold: float = 0.7,
    aoai_client: Optional[AzureOpenAIClient] = None,
    db: Optional[Database] = None,
    docintel: Optional[DocumentIntelligence] = None
) -> List[Dict[str, Any]]:
    """
    Use LLM to resolve validation issues for fields that:
    - Are missing
    - Have conflicts
    - Have low confidence scores

    Args:
        document_id: Document ID
        field_name: Optional specific field to resolve. If None, resolves all fields needing review.
        min_confidence_threshold: Minimum confidence threshold (default: 0.7)
        aoai_client: Optional AzureOpenAIClient instance
        db: Optional Database instance
        docintel: Optional DocumentIntelligence instance (for context extraction)

    Returns:
        List of resolution results
    """
    if aoai_client is None:
        aoai_client = AzureOpenAIClient()
    if db is None:
        db = Database()
    if docintel is None:
        docintel = DocumentIntelligence()

    session = db.get_session()
    try:
        # Get document
        document = session.query(Document).filter(Document.id == document_id).first()
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        # Get validation results that need LLM resolution
        query = session.query(ValidationResult).filter(
            ValidationResult.document_id == document_id,
            ValidationResult.status.in_([
                ValidationStatus.FAIL,
                ValidationStatus.NEEDS_REVIEW,
                ValidationStatus.PENDING
            ])
        )

        if field_name:
            query = query.filter(ValidationResult.field_name == field_name)

        validation_results = query.all()

        if not validation_results:
            return []

        # Get extraction result for context
        extraction_result = get_extraction_result(document_id, db=db)
        if extraction_result is None:
            raise ValueError(f"No extraction result found for document {document_id}")

        # Build document context
        context = _build_document_context(extraction_result, docintel)

        resolution_results = []

        for vr in validation_results:
            # Determine if LLM resolution is needed
            needs_resolution = (
                vr.status == ValidationStatus.FAIL or
                vr.status == ValidationStatus.NEEDS_REVIEW or
                (vr.confidence is not None and vr.confidence < min_confidence_threshold)
            )

            if not needs_resolution:
                continue

            # Get relevant context for this field
            field_context = _get_field_context(vr.field_name, extraction_result, context)

            # Resolve with LLM
            if vr.extracted_value is None or vr.status == ValidationStatus.FAIL:
                # Missing or failed - try to resolve
                resolution = aoai_client.resolve_field_conflict(
                    field_name=vr.field_name,
                    extracted_value=vr.extracted_value or "",
                    context=field_context,
                    validation_issue=vr.error_message or "Field validation failed"
                )

                # Update validation result
                vr.extracted_value = resolution.get("resolved_value") or vr.extracted_value
                vr.confidence = resolution.get("confidence", vr.confidence)
                vr.llm_resolution = resolution.get("reasoning", "")
                vr.updated_at = datetime.utcnow()

                # Update status based on resolution
                if resolution.get("resolved_value"):
                    if resolution.get("confidence", 0) >= min_confidence_threshold:
                        vr.status = ValidationStatus.PASS
                    else:
                        vr.status = ValidationStatus.NEEDS_REVIEW
                else:
                    vr.status = ValidationStatus.FAIL

            else:
                # Low confidence - validate with LLM
                validation_rules = _get_validation_rules_for_field(vr.field_name)
                llm_validation = aoai_client.validate_with_llm(
                    field_name=vr.field_name,
                    extracted_value=vr.extracted_value,
                    validation_rules=validation_rules,
                    document_context=field_context
                )

                # Update validation result
                vr.confidence = llm_validation.get("confidence", vr.confidence)
                vr.llm_resolution = llm_validation.get("reasoning", "")
                vr.updated_at = datetime.utcnow()

                if llm_validation.get("is_valid"):
                    vr.status = ValidationStatus.PASS
                else:
                    vr.status = ValidationStatus.NEEDS_REVIEW
                    if llm_validation.get("suggested_value"):
                        vr.extracted_value = llm_validation["suggested_value"]

            resolution_results.append({
                "field_name": vr.field_name,
                "status": vr.status.value,
                "confidence": vr.confidence,
                "resolved_value": vr.extracted_value,
                "reasoning": vr.llm_resolution
            })

        session.commit()
        return resolution_results

    finally:
        session.close()


def _build_document_context(
    extraction_result: Dict[str, Any],
    docintel: DocumentIntelligence
) -> str:
    """Build a text context from extraction result for LLM."""
    text_parts = []

    # Add text blocks (prioritize headings and important content)
    for block in extraction_result.get("text_blocks", []):
        content = block.get("content", "")
        if content:
            role = block.get("role", "")
            if role in ["title", "sectionHeading"]:
                text_parts.append(f"## {content}")
            else:
                text_parts.append(content)

    # Add table summaries
    for table in extraction_result.get("tables", []):
        table_text = []
        for cell in table.get("cells", []):
            if cell.get("content"):
                table_text.append(cell["content"])
        if table_text:
            text_parts.append(" | ".join(table_text))

    return "\n\n".join(text_parts)


def _get_field_context(
    field_name: str,
    extraction_result: Dict[str, Any],
    full_context: str
) -> str:
    """Get relevant context for a specific field."""
    # For now, return full context. In production, you might:
    # - Extract relevant sections based on field name
    # - Use semantic search to find most relevant paragraphs
    # - Include surrounding context from the document

    # Add field-specific hints
    field_hints = {
        "site_address": "Look for address information, postcodes, street names",
        "proposed_use": "Look for descriptions of proposed development, use classes",
        "application_ref": "Look for application reference numbers, planning references"
    }

    hint = field_hints.get(field_name, "")
    if hint:
        return f"{hint}\n\n{full_context}"

    return full_context


def _get_validation_rules_for_field(field_name: str) -> str:
    """Get validation rules description for a field (for LLM context)."""
    rules = {
        "site_address": "Site address must be a valid UK address with postcode",
        "proposed_use": "Proposed use must be clearly stated and match planning use classes",
        "application_ref": "Application reference must follow format APP/YYYY/NNNN"
    }

    return rules.get(field_name, f"Field {field_name} must be valid and complete")


# Field ownership: which doc types can extract which fields
DOC_FIELD_OWNERSHIP = {
    "application_form": {"application_ref", "site_address", "proposed_use", "applicant_name", "agent_name"},
    "site_plan": {"site_address", "proposed_use"},
    "drawing": {"proposed_use"},  # Drawings might have use descriptions
    "design_statement": {"proposed_use", "site_address"},
    "unknown": {"site_address", "proposed_use"},  # Fallback
}


def should_trigger_llm(
    validation: Dict[str, Any],
    extraction: Dict[str, Any],
    resolved_fields: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Check if LLM resolution should be triggered based on validation results.
    
    Only triggers if:
    - Missing field is extractable from THIS doc type (field ownership)
    - Doc has enough text coverage
    - At least one rule is blocking (severity error) - warnings don't trigger
    - Field hasn't already been resolved earlier in the run/application
    """
    resolved_fields = resolved_fields or {}
    
    # Check if needs_llm flag is set
    if not validation.get("summary", {}).get("needs_llm"):
        return False
    
    # Get document type
    doc_type = extraction.get("fields", {}).get("document_type", "unknown")
    
    # Get missing fields from validation findings (only errors, not warnings)
    missing_fields = []
    has_error_severity = False
    
    for finding in validation.get("findings", []):
        # Only consider error severity for LLM trigger
        if finding.get("severity") != "error":
            continue
            
        if finding.get("status") in ["needs_review", "fail"]:
            missing = finding.get("missing_fields", [])
            # Skip if field already resolved
            missing = [f for f in missing if f not in resolved_fields]
            missing_fields.extend(missing)
            has_error_severity = True
    
    if not missing_fields or not has_error_severity:
        return False
    
    # Check field ownership: only extract fields this doc type can provide
    allowed_fields = DOC_FIELD_OWNERSHIP.get(doc_type, set())
    missing_allowed = [f for f in missing_fields if f in allowed_fields]
    
    if not missing_allowed:
        return False
    
    # Check text coverage (at least some text blocks)
    text_blocks = extraction.get("text_blocks", [])
    if len(text_blocks) < 5:  # Too little text to justify LLM
        return False
    
    return True


def build_llm_prompt(extraction: Dict[str, Any], validation: Dict[str, Any]) -> Dict[str, Any]:
    """Build LLM prompt for resolving missing fields."""
    # Keep it schema-bound: ask for missing fields only.
    missing_fields: List[str] = []
    for f in validation.get("findings", []):
        missing_fields.extend(f.get("missing_fields", []))
    missing_fields = sorted(set(missing_fields))

    return {
        "task": "Fill missing structured fields from extracted evidence only. If not found, return null.",
        "missing_fields": missing_fields,
        "extraction_fields": extraction.get("fields", {}),
        "evidence_index": extraction.get("evidence_index", {}),
        "return_schema": {
            "filled_fields": {k: "string|number|object|null" for k in missing_fields},
            "notes": "string",
            "citations": [
                {
                    "field": "string",
                    "evidence_key": "string",
                    "page": "number",
                    "quote": "string"
                }
            ],
        },
    }


def resolve_with_llm_new(extraction: Dict[str, Any], validation: Dict[str, Any], aoai_client: Optional[AzureOpenAIClient] = None) -> Dict[str, Any]:
    """
    Use LLM to resolve missing fields from extraction and validation results.
    
    Args:
        extraction: Extraction result dictionary
        validation: Validation result dictionary
        aoai_client: Optional AzureOpenAIClient instance
        
    Returns:
        Dictionary with triggered flag, request, response, and gate logging info
    """
    if aoai_client is None:
        aoai_client = AzureOpenAIClient()
    
    # Collect missing fields and affected rule IDs for logging
    missing_fields: List[str] = []
    affected_rule_ids: List[str] = []
    
    for finding in validation.get("findings", []):
        if finding.get("status") in ["needs_review", "fail"]:
            missing = finding.get("missing_fields", [])
            missing_fields.extend(missing)
            rule_id = finding.get("rule_id")
            if rule_id:
                affected_rule_ids.append(rule_id)
    
    missing_fields = sorted(set(missing_fields))
    affected_rule_ids = sorted(set(affected_rule_ids))
    
    prompt_obj = build_llm_prompt(extraction, validation)
    resp = aoai_client.chat_json(prompt_obj)  # returns parsed JSON dict
    
    return {
        "triggered": True,
        "gate_reason": {
            "missing_fields": missing_fields,
            "affected_rule_ids": affected_rule_ids,
            "validation_summary": validation.get("summary", {})
        },
        "request": prompt_obj,
        "response": resp,
    }

