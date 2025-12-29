"""
Extract module: Use Document Intelligence to extract structured data from documents.
"""

import json as jsonlib
from typing import Dict, Any, Optional
from datetime import datetime

from planproof.docintel import DocumentIntelligence
from planproof.storage import StorageClient
from planproof.db import Database, Document, Artefact


def extract_document(
    document_id: int,
    model: str = "prebuilt-layout",
    docintel: Optional[DocumentIntelligence] = None,
    storage_client: Optional[StorageClient] = None,
    db: Optional[Database] = None
) -> Dict[str, Any]:
    """
    Extract structured data from a document using Document Intelligence.

    Args:
        document_id: Document ID from database
        model: Document Intelligence model to use (default: "prebuilt-layout")
        docintel: Optional DocumentIntelligence instance
        storage_client: Optional StorageClient instance
        db: Optional Database instance

    Returns:
        Dictionary with:
        - artefact_id: Created artefact ID
        - artefact_blob_uri: Blob URI of stored JSON artefact
        - extraction_result: The extraction result dictionary
    """
    # Initialize clients if not provided
    if docintel is None:
        docintel = DocumentIntelligence()
    if storage_client is None:
        storage_client = StorageClient()
    if db is None:
        db = Database()

    # Get document from database
    session = db.get_session()
    try:
        document = session.query(Document).filter(Document.id == document_id).first()
        if document is None:
            raise ValueError(f"Document not found: {document_id}")

        # Extract blob URI components
        # Format: azure://{account}/{container}/{blob_name}
        blob_uri_parts = document.blob_uri.replace("azure://", "").split("/", 2)
        if len(blob_uri_parts) != 3:
            raise ValueError(f"Invalid blob URI format: {document.blob_uri}")

        container = blob_uri_parts[1]
        blob_name = blob_uri_parts[2]

        # Download PDF from blob storage
        pdf_bytes = storage_client.download_blob(container, blob_name)

        # Analyze document with Document Intelligence
        extraction_result = docintel.analyze_document(pdf_bytes, model=model)

        # Update document metadata
        document.page_count = extraction_result["metadata"]["page_count"]
        document.docintel_model = model
        document.processed_at = datetime.utcnow()

        # Store extraction result as JSON artefact
        # Ensure the result is fully serializable (deep copy to remove any object references)
        import copy as copy_module
        extraction_result_clean = copy_module.deepcopy(extraction_result)
        artefact_name = f"extracted_layout_{document_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        artefact_blob_uri = storage_client.write_artefact(extraction_result_clean, artefact_name)

        # Create artefact record
        artefact = Artefact(
            document_id=document_id,
            artefact_type="extracted_layout",
            blob_uri=artefact_blob_uri,
            artefact_metadata={
                "model": model,
                "extracted_at": datetime.utcnow().isoformat()
            }
        )
        session.add(artefact)
        session.commit()
        session.refresh(artefact)

        return {
            "artefact_id": artefact.id,
            "artefact_blob_uri": artefact_blob_uri,
            "extraction_result": extraction_result
        }

    finally:
        session.close()


def get_extraction_result(
    document_id: int,
    storage_client: Optional[StorageClient] = None,
    db: Optional[Database] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the most recent extraction result for a document.

    Args:
        document_id: Document ID
        storage_client: Optional StorageClient instance
        db: Optional Database instance

    Returns:
        Extraction result dictionary or None if not found
    """
    if storage_client is None:
        storage_client = StorageClient()
    if db is None:
        db = Database()

    session = db.get_session()
    try:
        # Get most recent extracted_layout artefact
        artefact = (
            session.query(Artefact)
            .filter(
                Artefact.document_id == document_id,
                Artefact.artefact_type == "extracted_layout"
            )
            .order_by(Artefact.created_at.desc())
            .first()
        )

        if artefact is None:
            return None

        # Extract blob URI components and download
        blob_uri_parts = artefact.blob_uri.replace("azure://", "").split("/", 2)
        if len(blob_uri_parts) != 3:
            return None

        container = blob_uri_parts[1]
        blob_name = blob_uri_parts[2]

        artefact_bytes = storage_client.download_blob(container, blob_name)
        return jsonlib.loads(artefact_bytes.decode("utf-8"))

    finally:
        session.close()


def extract_from_pdf_bytes(
    pdf_bytes: bytes,
    document_meta: Dict[str, Any],
    model: str = "prebuilt-layout",
    docintel: Optional[DocumentIntelligence] = None
) -> Dict[str, Any]:
    """
    Extract structured data from PDF bytes (for use in end-to-end pipeline).

    Args:
        pdf_bytes: PDF file content as bytes
        document_meta: Dictionary with document metadata (e.g., from ingest)
        model: Document Intelligence model to use
        docintel: Optional DocumentIntelligence instance

    Returns:
        Extraction result dictionary with fields and evidence_index
    """
    if docintel is None:
        docintel = DocumentIntelligence()

    # Analyze document with Document Intelligence
    extraction_result = docintel.analyze_document(pdf_bytes, model=model)

    # Use field mapper to extract structured fields
    from planproof.pipeline.field_mapper import map_fields
    
    mapped = map_fields(extraction_result)
    fields = mapped["fields"]
    field_evidence = mapped["evidence_index"]
    
    # Build general evidence_index for text blocks and tables
    evidence_index = {}
    
    # Extract text blocks as evidence with page numbers and snippets
    for i, block in enumerate(extraction_result.get("text_blocks", [])):
        content = block.get("content", "")
        page_num = block.get("page_number")
        # Create snippet (first 100 chars)
        snippet = content[:100] + "..." if len(content) > 100 else content
        
        evidence_key = f"text_block_{i}"
        evidence_index[evidence_key] = {
            "type": "text_block",
            "content": content,
            "snippet": snippet,
            "page_number": page_num,
            "bounding_box": block.get("bounding_box")
        }
        
        # Add index to block for field mapper reference
        block["index"] = i

    # Extract tables as evidence with page numbers
    for i, table in enumerate(extraction_result.get("tables", [])):
        page_num = table.get("page_number")
        # Create snippet from first few cells
        cells = table.get("cells", [])
        cell_snippets = []
        for cell in cells[:5]:  # First 5 cells
            if cell.get("content"):
                cell_snippets.append(cell["content"][:50])
        snippet = " | ".join(cell_snippets) if cell_snippets else ""
        
        evidence_key = f"table_{i}"
        evidence_index[evidence_key] = {
            "type": "table",
            "row_count": table.get("row_count"),
            "column_count": table.get("column_count"),
            "page_number": page_num,
            "snippet": snippet,
            "cells": cells
        }
    
    # Merge field-specific evidence into general evidence_index
    for field_name, ev_list in field_evidence.items():
        evidence_index[field_name] = ev_list

    return {
        "fields": fields,
        "evidence_index": evidence_index,
        "metadata": extraction_result.get("metadata", {}),
        "text_blocks": extraction_result.get("text_blocks", []),
        "tables": extraction_result.get("tables", []),
        "page_anchors": extraction_result.get("page_anchors", {})
    }

